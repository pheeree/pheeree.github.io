#!/Users/pheeree/miniconda3/bin/python3
"""블로그 포스트의 서지정보 + 원문 링크를 모아 _data/citations.yml 로 빌드.

산출:
  _data/citations.yml   — 글별 서지(중심 논문 + 본문 인용), 기계 판독용 단일 출처
  bibliography.md       — citations.yml 을 사람이 읽게 렌더한 페이지

옵션:
  python scripts/build_citations.py                       # citations.yml + bibliography.md 생성
  python scripts/build_citations.py --link-posts          # 위 + 본문 평문 arXiv를 검증된 것만 하이퍼링크화
  python scripts/build_citations.py --check               # 생성하지 않고 통계만
  python scripts/build_citations.py --check-links         # 본문·다음후보 링크 누락 보고 (발행 게이트, 누락 시 exit 1)
  python scripts/build_citations.py --verify-draft <파일>  # 드래프트 한 편의 id 실재 검증 (환각 id 경고, 비차단)

본문 평문 세 형식 모두 링크화 (--link-posts):
  1) arXiv:NNNN.NNNNN          2) 괄호 평문 (NNNN.NNNNN)    3) 맨 arXiv URL
  각주(`[^`)·코드블록·이미 링크된 것은 건드리지 않는다.

검증 정책 (죽은 링크 0):
  - 신뢰 위계: arxiv-cache(미러, 우리 PDF) → 로컬 resolve 캐시 → arxiv.org HEAD 실재 확인.
  - **실재 확인은 HEAD(arxiv.org/abs)로 한다** — 메타데이터 API(export.arxiv.org)가 막힌 환경에서도
    동작. 메타 API(제목·저자)는 best-effort 보너스이며 실패해도 링크는 단다.
  - 404(부재)는 로컬 캐시에 not_found 로 영속 기록 → 환각·오태 id 재조회 방지 + verify-draft 경고.
  - 검증된 id 만 링크화. resolve 캐시는 배치/건마다 증분 저장(중단 내성, rate-limit 완화).

설계:
  - 블로그 레포 자기완결. KM 미러의 arxiv-cache 는 읽되 없으면 건너뜀(선택적 의존).
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
POSTS = REPO / "_posts"
DATA_DIR = REPO / "_data"
OUT_YML = DATA_DIR / "citations.yml"
OUT_BIB = REPO / "bibliography.md"
# KM 미러의 arxiv 메타 캐시 (선택적 — 없으면 전부 API 로).
MIRROR_CACHE = Path.home() / "Mirrors/knowledge-mind/raw/arxiv-cache.json"
# 로컬 resolve 캐시 — 한 번 조회한 id(실재·부재 모두)를 영속화해 arXiv 429 rate limit 완화.
# 부재(죽은 id)도 기록해 재조회를 막는다. 미러 cache 와 별개로 블로그 레포가 자체 보유.
RESOLVE_CACHE = REPO / "_data" / "arxiv-resolved.json"

ARXIV_ID = re.compile(r"\b(\d{4}\.\d{4,5})(v\d+)?\b")
ARXIV_MENTION = re.compile(r"arXiv:(\d{4}\.\d{4,5})(v\d+)?", re.IGNORECASE)
# 접두어 없는 괄호 id `(2510.19771)` — '다음 읽을 후보'에 흔한 형식. 오태(연도.숫자) 방지 위해
#   링크 시점에 arXiv 실재 확인된 id 만 채택한다.
BARE_PAREN_ID = re.compile(r"\((\d{4}\.\d{4,5})(v\d+)?\)")
# 맨 arXiv URL (마크다운 링크 ( ) 안이 아닌 것) — 작성 에이전트가 링크 대신 raw URL 단 경우.
RAW_ARXIV_URL = re.compile(r"(?<![(\]])https?://arxiv\.org/(?:abs|html|pdf)/(\d{4}\.\d{4,5})(v\d+)?\S*")
# 비-arXiv 학술 맨 URL (openreview·aclanthology·nips 등). 자동 링크화 대상은 아니나 게이트가 경고.
RAW_OTHER_URL = re.compile(
    r"(?<![(\]])https?://(?:openreview\.net|aclanthology\.org|proceedings\.\w+|papers\.nips\.cc|dl\.acm\.org)\S*"
)
SOURCE_LINE = re.compile(r'^source:\s*["\']?PAPER/(\d{4}\.\d{4,5})', re.MULTILINE)
FM_TITLE = re.compile(r'^title:\s*["\']?(.+?)["\']?\s*$', re.MULTILINE)

USER_AGENT = "pheeree-blog/1.0 (mailto:pheeree@gmail.com)"
RETRY_MAX = 3
RETRY_BACKOFF = (30, 60, 120)
# 한 요청에 id 를 너무 많이 실으면(관측상 200개 안팎) 일부가 응답에서 조용히 누락된다 —
# 실측: 221개 한 배치에서 21개 누락, 그 21개만 단독 조회하면 전부 성공. 청크로 나눠 회피.
META_BATCH_SIZE = 50
NS = {"a": "http://www.w3.org/2005/Atom"}


# ---------- arXiv 조회 ----------

def load_mirror_cache() -> dict:
    if not MIRROR_CACHE.exists():
        return {}
    try:
        return json.loads(MIRROR_CACHE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def load_resolve_cache() -> dict:
    """로컬 resolve 캐시. {id: {title,authors,published,categories}} 또는 {id: {not_found: true}}.
    title·categories 가 빈 문자열/리스트인 항목은 "실재는 확인됐으나 메타 미상"으로,
    영구 확정이 아니라 매 실행 재시도 대상이다(resolve_ids 참고)."""
    if not RESOLVE_CACHE.exists():
        return {}
    try:
        return json.loads(RESOLVE_CACHE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_resolve_cache(rc: dict) -> None:
    RESOLVE_CACHE.parent.mkdir(exist_ok=True)
    RESOLVE_CACHE.write_text(json.dumps(rc, ensure_ascii=False, indent=1), encoding="utf-8")


def head_exists(arxiv_id: str) -> bool | None:
    """arxiv.org/abs/{id} HEAD 로 실재 확인. True=실재, False=부재(404), None=불확정(네트워크 실패).
    메타데이터 API(export.arxiv.org)가 막힌 환경에서도 실재 확인은 이 경로로 빠르게(0.1초) 된다."""
    url = f"https://arxiv.org/abs/{arxiv_id}"
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return 200 <= r.status < 300
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        return None  # 403·429 등은 불확정 — 죽은 id 로 굳히지 않는다
    except (TimeoutError, urllib.error.URLError):
        return None


def fetch_meta_batch(ids: list[str]) -> dict[str, dict]:
    """arXiv 메타데이터 API 배치 조회(제목·저자·카테고리). best-effort — 막힌 환경에선 빈 dict 반환.
    실재 확인은 head_exists 가 담당하고, 이쪽은 제목 보강용 보너스다.
    429(rate limit)는 RETRY_BACKOFF 로 재시도 — 침묵 실패로 영구 캐시되지 않게 한다."""
    if not ids:
        return {}
    q = urllib.parse.urlencode({"id_list": ",".join(ids), "max_results": len(ids)})
    url = f"http://export.arxiv.org/api/query?{q}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    data = None
    for attempt in range(RETRY_MAX):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read().decode("utf-8")
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < RETRY_MAX - 1:
                time.sleep(RETRY_BACKOFF[attempt])
                continue
            return {}  # 재시도 소진 또는 429 외 오류 — best-effort 실패
        except Exception:
            return {}
    if data is None:
        return {}

    out = {}
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return {}
    for entry in root.findall("a:entry", NS):
        full_id = entry.find("a:id", NS).text.strip()
        arxiv_id = full_id.split("/abs/")[-1]
        base_id = re.sub(r"v\d+$", "", arxiv_id)
        title = " ".join((entry.find("a:title", NS).text or "").split())
        authors = [
            (a.find("a:name", NS).text or "").strip()
            for a in entry.findall("a:author", NS)
        ]
        published = (entry.find("a:published", NS).text or "")[:10]
        categories = [
            c.get("term", "") for c in entry.findall("a:category", NS) if c.get("term")
        ]
        out[base_id] = {
            "title": title, "authors": authors, "published": published,
            "categories": categories,
        }
    return out


def resolve_ids(ids: set[str], cache: dict, do_fetch: bool) -> dict[str, dict]:
    """id → 메타. 신뢰 위계: 미러 cache → 로컬 resolve 캐시 → (실재) HEAD + (제목) 메타 API.
    실재 확인은 HEAD(arxiv.org/abs)로 — export.arxiv.org 가 막힌 환경에서도 동작.
    메타데이터 API 는 best-effort 보너스. 실재 확인된 id 는 제목이 없어도 resolved 에 넣어 링크는 단다.
    부재(404)는 로컬 캐시에 not_found 로 영속 기록해 재조회를 막는다.
    **제목·카테고리(키워드)가 빈 항목은 영구 확정이 아니라 매 실행 재시도 대상**(미러 캐시가
    카테고리를 안 주는 경우 포함, 신·구 로컬 캐시 형식 모두) — 한 번의 rate limit·네트워크 실패,
    또는 미러 캐시 쪽 메타 부재가 정보를 영원히 비워두지 않는다."""
    resolved = {}
    rc = load_resolve_cache()
    missing = []
    for i in ids:
        entry = cache.get(i)
        rentry = rc.get(i)
        if entry and not entry.get("not_found"):
            # 미러가 카테고리를 안 주면, 예전에 우리 쪽 API 조회로 이미 받아 둔 게 있는지 먼저 본다
            # (없으면 매 실행 똑같이 재조회하게 됨).
            cats = entry.get("categories") or (rentry or {}).get("categories", [])
            resolved[i] = {
                "title": entry.get("title", ""),
                "authors": entry.get("authors", []),
                "published": entry.get("published", ""),
                "categories": cats,
            }
            if not resolved[i]["title"] or not resolved[i]["categories"]:
                missing.append(i)  # 미러·로컬 캐시 모두 카테고리 없음 — 보강 시도(제목은 보존)
            continue
        if rentry is not None:
            if rentry.get("not_found"):
                continue  # 죽은 id — 재조회 안 함
            resolved[i] = {
                "title": rentry.get("title", ""),
                "authors": rentry.get("authors", []),
                "published": rentry.get("published", ""),
                "categories": rentry.get("categories", []),
            }
            if not rentry.get("title") or not rentry.get("categories"):
                missing.append(i)  # 제목·카테고리 미상 — 이번 실행에서 재시도
            continue
        missing.append(i)

    if do_fetch and missing:
        # 1) 제목·카테고리 보강: 메타 API 청크 조회(429 는 내부에서 재시도, 그래도 막히면 빈 dict).
        # 큰 배치는 일부 id가 응답에서 조용히 빠지는 게 실측돼 META_BATCH_SIZE 로 나눈다.
        meta = {}
        for start in range(0, len(missing), META_BATCH_SIZE):
            chunk = missing[start:start + META_BATCH_SIZE]
            meta.update(fetch_meta_batch(chunk))
        # 2) 실재 확인: id 별 HEAD (빠름·안정). meta 에 있으면 실재 확정이라 HEAD 생략.
        for cid in missing:
            if cid in meta:
                rc[cid] = meta[cid]
                resolved[cid] = meta[cid]
                save_resolve_cache(rc)
                continue
            if cid in resolved:
                # 이미 값이 있음(미러 유래 제목 등) — 메타 보강만 실패했을 뿐이니 기존 값 보존.
                continue
            exists = head_exists(cid)
            if exists is True:
                rc[cid] = {"title": "", "authors": [], "published": "", "categories": []}
                resolved[cid] = rc[cid]
            elif exists is False:
                rc[cid] = {"not_found": True}  # 404 — 환각·오태, 영속 기록
            # exists is None → 불확정(네트워크 실패): 캐시에 안 굳히고 다음 실행 재시도
            save_resolve_cache(rc)  # 건마다 증분 저장 — 중단돼도 성과 보존

    return resolved


# ---------- 포스트 파싱 ----------

def post_slug(path: Path) -> str:
    return path.stem


def collect_ids_from_post(text: str) -> tuple[str | None, set[str]]:
    """(중심 논문 id 또는 None, 본문 등장 모든 id set).
    세 형식 모두 수집 — arXiv:id / 괄호 id (2510.19771) / 맨 arXiv URL.
    괄호 id는 오태(연도.숫자) 위험이 있으나, 후속 resolve 단계에서 arXiv 실재 확인으로 걸러진다."""
    central = None
    m = SOURCE_LINE.search(text)
    if m:
        central = m.group(1)
    body_ids = {m.group(1) for m in ARXIV_MENTION.finditer(text)}
    body_ids |= {m.group(1) for m in BARE_PAREN_ID.finditer(text)}
    body_ids |= {m.group(1) for m in RAW_ARXIV_URL.finditer(text)}
    if central:
        body_ids.add(central)
    return central, body_ids


def authors_short(authors: list[str]) -> str:
    if not authors:
        return ""
    if len(authors) <= 2:
        return ", ".join(authors)
    return f"{authors[0]} 외"


# ---------- 산출: citations.yml ----------

def yaml_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def build_yml(posts_meta: list[dict]) -> str:
    lines = [
        "# 자동 생성 — scripts/build_citations.py. 직접 편집 금지.",
        "# 글별 서지정보 + 원문 링크. 포스트 발행 때마다 갱신.",
        "",
    ]
    for pm in posts_meta:
        lines.append(f"{pm['slug']}:")
        if pm.get("title"):
            lines.append(f'  title: "{yaml_escape(pm["title"])}"')
        c = pm.get("central")
        if c:
            lines.append("  central:")
            lines.append(f'    id: "{c["id"]}"')
            lines.append(f'    title: "{yaml_escape(c["title"])}"')
            if c.get("authors"):
                lines.append(f'    authors: "{yaml_escape(c["authors"])}"')
            if c.get("keywords"):
                lines.append(f'    keywords: "{yaml_escape(", ".join(c["keywords"]))}"')
            lines.append(f'    url: "{c["url"]}"')
        refs = pm.get("referenced", [])
        if refs:
            lines.append("  referenced:")
            for r in refs:
                title = f', title: "{yaml_escape(r["title"])}"' if r.get("title") else ""
                authors = f', authors: "{yaml_escape(r["authors"])}"' if r.get("authors") else ""
                keywords = (
                    f', keywords: "{yaml_escape(", ".join(r["keywords"]))}"'
                    if r.get("keywords") else ""
                )
                lines.append(
                    f'    - {{ id: "{r["id"]}"{title}{authors}{keywords}, url: "{r["url"]}" }}'
                )
        lines.append("")
    return "\n".join(lines)


def build_bibliography(posts_meta: list[dict]) -> str:
    lines = [
        "---",
        "layout: page",
        "title: 서지정보 (Bibliography)",
        "permalink: /bibliography/",
        "---",
        "",
        "이 페이지는 각 글이 인용한 논문의 서지정보와 원문 링크를 모은다. "
        "`scripts/build_citations.py` 가 자동 생성하며 발행 때마다 갱신된다.",
        "",
    ]
    for pm in posts_meta:
        if not (pm.get("central") or pm.get("referenced")):
            continue
        date = pm["slug"][:10]
        title = pm.get("title", pm["slug"])
        lines.append(f"## [{date}] {title}")
        lines.append("")
        c = pm.get("central")
        if c:
            who = f"{c['authors']}. " if c.get("authors") else ""
            kw = f" — 키워드: {', '.join(c['keywords'])}" if c.get("keywords") else ""
            lines.append(f"- **중심**: {who}*{c['title']}*. [arXiv:{c['id']}]({c['url']}){kw}")
        for r in pm.get("referenced", []):
            who = f"{r['authors']}. " if r.get("authors") else ""
            t = f"*{r['title']}*. " if r.get("title") else ""
            kw = f" — 키워드: {', '.join(r['keywords'])}" if r.get("keywords") else ""
            lines.append(f"- {who}{t}[arXiv:{r['id']}]({r['url']}){kw}")
        lines.append("")
    return "\n".join(lines)


# ---------- 본문 링크화 ----------

def _linkable_lines(text: str):
    """(idx, line) 중 링크 대상 줄만 yield — 코드블록·각주 정의 줄 제외."""
    in_fence = False
    for idx, line in enumerate(text.split("\n")):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or stripped.startswith("[^"):
            continue
        yield idx, line


def link_post_body(text: str, valid_ids: set[str]) -> tuple[str, int]:
    """본문의 평문 arXiv 인용을 검증된 id 만 하이퍼링크화. 세 형식 처리:
      1) `arXiv:ID`            → `[arXiv:ID](url)`
      2) `(ID)` 괄호 평문       → `([arXiv:ID](url))`  (실재 확인된 id 만)
      3) 맨 `https://arxiv.org/abs/ID` → `[arXiv:ID](url)`
    각주 정의 줄·코드블록·이미 링크된 것은 제외."""
    lines = text.split("\n")
    targets = dict(_linkable_lines(text))
    changed = 0

    for idx, line in targets.items():
        # 3) 맨 arXiv URL 먼저 (URL 안 숫자가 다른 패턴에 안 걸리게)
        def repl_url(m):
            nonlocal changed
            base = m.group(1)
            if base not in valid_ids:
                return m.group(0)
            changed += 1
            return f"[arXiv:{base}](https://arxiv.org/abs/{base})"
        line = RAW_ARXIV_URL.sub(repl_url, line)

        # 1) arXiv:ID
        def repl_mention(m):
            nonlocal changed
            base, ver = m.group(1), m.group(2) or ""
            if base not in valid_ids:
                return m.group(0)
            if m.start() > 0 and line[m.start() - 1] == "[":
                return m.group(0)  # 이미 링크 텍스트
            changed += 1
            return f"[arXiv:{base}{ver}](https://arxiv.org/abs/{base})"
        line = ARXIV_MENTION.sub(repl_mention, line)

        # 2) 괄호 평문 (ID) — 실재 확인된 id 만. 이미 [arXiv 로 시작하는 링크 괄호는 건드리지 않음.
        def repl_bare(m):
            nonlocal changed
            base, ver = m.group(1), m.group(2) or ""
            if base not in valid_ids:
                return m.group(0)
            # 바로 앞이 ']' 면 마크다운 링크 꼬리 `](...)` 일 수 있음 — 건너뜀
            if m.start() > 0 and line[m.start() - 1] == "]":
                return m.group(0)
            changed += 1
            return f"([arXiv:{base}{ver}](https://arxiv.org/abs/{base}))"
        line = BARE_PAREN_ID.sub(repl_bare, line)

        lines[idx] = line
    return "\n".join(lines), changed


def find_unlinked(text: str, valid_ids: set[str]) -> list[tuple[int, str]]:
    """링크 안 된 채 남은 검증된 arXiv 인용을 (줄번호, 스니펫)으로 반환.
    --check-links 게이트용. 각주·코드는 의도적 제외라 보지 않는다."""
    out = []
    for idx, line in _linkable_lines(text):
        for m in ARXIV_MENTION.finditer(line):
            if m.group(1) in valid_ids and not (m.start() > 0 and line[m.start() - 1] == "["):
                out.append((idx + 1, line.strip()[:80]))
                break
        else:
            for m in BARE_PAREN_ID.finditer(line):
                if m.group(1) in valid_ids and not (m.start() > 0 and line[m.start() - 1] == "]"):
                    out.append((idx + 1, line.strip()[:80]))
                    break
            else:
                if RAW_ARXIV_URL.search(line):
                    out.append((idx + 1, line.strip()[:80]))
    # 비-arXiv 맨 URL (openreview·aclanthology 등) — 마크다운 링크 아닌 raw
    for idx, line in _linkable_lines(text):
        if RAW_OTHER_URL.search(line):
            out.append((idx + 1, "[비-arXiv 맨 URL] " + line.strip()[:65]))
    return out


# 중심 논문(source) 링크가 '오늘의 한 편' 섹션에 있는지 점검용.
TODAY_SECTION = re.compile(r"##\s*오늘의 한 편(.*?)(?=\n##\s|\Z)", re.S)
ARXIV_MD_LINK = re.compile(r"\]\(https?://arxiv\.org/abs/(\d{4}\.\d{4,5})")


def check_central_link(text: str) -> str | None:
    """'오늘의 한 편' 섹션에 중심 논문(source PAPER/id) 하이퍼링크가 있는지.
    누락이면 중심 id 반환, 정상이면 None. arXiv 아닌 source(노트 기반 글)는 대상 외(None)."""
    m = SOURCE_LINE.search(text)
    if not m:
        return None  # arXiv 중심 논문 아님 — 대상 외
    cid = m.group(1)
    sec = TODAY_SECTION.search(text)
    body = sec.group(1) if sec else ""
    if cid in set(ARXIV_MD_LINK.findall(body)):
        return None
    return cid


def verify_draft(path: Path, cache: dict) -> int:
    """드래프트 한 편의 본문 arXiv id 를 실재 확인. 실재 안 하는 id(환각·추정 추정)를 경고.
    비차단 — 경고만 출력하고 발행은 막지 않는다. 반환: 의심 id 수."""
    text = path.read_text(encoding="utf-8")
    _, ids = collect_ids_from_post(text)
    if not ids:
        print(f"  (arXiv 인용 없음: {path.name})")
        return 0
    resolved = resolve_ids(ids, cache, do_fetch=True)
    dead = sorted(ids - set(resolved.keys()))
    print(f"=== 드래프트 id 실재 검증: {path.name} ===")
    print(f"  본문 arXiv id {len(ids)}개 중 실재 확인 {len(resolved)}, 미확인 {len(dead)}")
    if dead:
        print(f"  ⚠ 실재 확인 안 됨 (환각·추정·미래 id 의심 — 본문 대조 권장):")
        for d in dead:
            # 그 id 가 본문 어디서 쓰였는지 한 줄 보여줌
            for ln in text.split("\n"):
                if d in ln:
                    print(f"      {d}: {ln.strip()[:75]}")
                    break
        print("  → claim-check 와 함께 검토. 비차단 — 발행은 진행됨.")
    else:
        print("  ✓ 본문 arXiv id 전부 실재 확인됨.")
    # '오늘의 한 편' 중심 논문 링크 점검
    cmiss = check_central_link(text)
    if cmiss:
        print(f"  ⚠ '오늘의 한 편'에 중심 논문 {cmiss} 하이퍼링크 누락 — `[arXiv:{cmiss}](https://arxiv.org/abs/{cmiss})` 추가 권장.")
    return len(dead)


# ---------- main ----------

def main() -> None:
    check_only = "--check" in sys.argv
    link_posts = "--link-posts" in sys.argv
    check_links = "--check-links" in sys.argv
    # --verify-draft <파일경로>: 드래프트 한 편의 id 실재 검증 (B-3 저장 직후용)
    if "--verify-draft" in sys.argv:
        i = sys.argv.index("--verify-draft")
        draft = Path(sys.argv[i + 1]) if i + 1 < len(sys.argv) else None
        if not draft or not draft.exists():
            print("사용: build_citations.py --verify-draft <드래프트.md>", file=sys.stderr)
            sys.exit(2)
        verify_draft(draft, load_mirror_cache())
        sys.exit(0)

    cache = load_mirror_cache()
    posts = sorted(POSTS.glob("*.md"), reverse=True)

    # 1차 패스: 모든 id 수집
    all_ids = set()
    parsed = []
    for p in posts:
        text = p.read_text(encoding="utf-8")
        central, ids = collect_ids_from_post(text)
        tm = FM_TITLE.search(text)
        parsed.append({
            "path": p, "slug": post_slug(p), "text": text,
            "central_id": central, "ids": ids,
            "title": tm.group(1) if tm else "",
        })
        all_ids |= ids

    # id 해소 (cache + API). check_links 도 실재 확인이 필요하므로 fetch 한다.
    resolved = resolve_ids(all_ids, cache, do_fetch=not check_only)

    # --check-links: 본문/다음후보 링크 누락 + '오늘의 한 편' 중심 링크 누락을 보고. 발행 전 게이트.
    if check_links:
        valid_ids = set(resolved.keys())
        total = 0
        central_miss = 0
        for pp in parsed:
            miss = find_unlinked(pp["text"], valid_ids)
            cmiss = check_central_link(pp["text"])
            if miss or cmiss:
                print(f"⚠ {pp['slug']}")
                for ln, snip in miss:
                    print(f"    L{ln}: {snip}")
                    total += 1
                if cmiss:
                    print(f"    [오늘의 한 편] 중심 논문 {cmiss} 링크 누락")
                    central_miss += 1
        if total == 0 and central_miss == 0:
            print("✓ 누락 없음 — 본문·다음후보 검증 인용 + 오늘의 한 편 중심 링크 모두 정상.")
            sys.exit(0)
        print(f"\n✗ 링크 안 된 검증 인용 {total}건, 중심 링크 누락 {central_miss}건. `--link-posts` 로 보완 가능.")
        sys.exit(1)

    if check_only:
        in_cache = sum(1 for i in all_ids if i in cache and not cache[i].get("not_found"))
        print("=== citations 빌드 통계 (생성 안 함) ===")
        print(f"포스트: {len(parsed)}편")
        print(f"고유 arXiv id: {len(all_ids)}개")
        print(f"  cache 보유(검증됨): {in_cache}")
        print(f"  cache 외(API 필요): {len(all_ids) - in_cache}")
        print("(--link-posts 없이 본문 미수정)")
        return

    # posts_meta 구성
    posts_meta = []
    for pp in parsed:
        pm = {"slug": pp["slug"], "title": pp["title"]}
        cid = pp["central_id"]
        if cid and cid in resolved:
            r = resolved[cid]
            pm["central"] = {
                "id": cid, "title": r["title"],
                "authors": authors_short(r["authors"]),
                "keywords": r.get("categories", []),
                "url": f"https://arxiv.org/abs/{cid}",
            }
        refs = []
        for i in sorted(pp["ids"]):
            if i == cid:
                continue
            if i in resolved:
                r = resolved[i]
                refs.append({
                    "id": i, "title": r["title"],
                    "authors": authors_short(r.get("authors", [])),
                    "keywords": r.get("categories", []),
                    "url": f"https://arxiv.org/abs/{i}",
                })
        pm["referenced"] = refs
        posts_meta.append(pm)

    DATA_DIR.mkdir(exist_ok=True)
    OUT_YML.write_text(build_yml(posts_meta), encoding="utf-8")
    OUT_BIB.write_text(build_bibliography(posts_meta), encoding="utf-8")

    valid_ids = set(resolved.keys())
    total_refs = sum(len(pm.get("referenced", [])) for pm in posts_meta)
    n_central = sum(1 for pm in posts_meta if pm.get("central"))
    print(f"작성 완료: {OUT_YML.name} + {OUT_BIB.name}")
    print(f"  포스트 {len(posts_meta)}편, 중심 논문 {n_central}편, 참조 링크 {total_refs}개")
    print(f"  검증된 고유 id: {len(valid_ids)} / 전체 {len(all_ids)}")

    if link_posts:
        linked_posts = 0
        linked_total = 0
        residual = 0
        for pp in parsed:
            new_text, n = link_post_body(pp["text"], valid_ids)
            if n > 0:
                pp["path"].write_text(new_text, encoding="utf-8")
                linked_posts += 1
                linked_total += n
            # 처리 후에도 링크 안 된 검증 인용이 남으면 보고 (침묵 금지).
            left = find_unlinked(new_text, valid_ids)
            if left:
                residual += len(left)
                for ln, snip in left:
                    print(f"  · 잔존 미링크 {pp['slug']} L{ln}: {snip}", file=sys.stderr)
        print(f"본문 링크화: {linked_posts}편에서 {linked_total}개 평문 arXiv → 하이퍼링크")
        if residual:
            print(f"⚠ 처리 후 잔존 미링크 {residual}건 (위 stderr 목록) — 패턴 확장 필요 신호.")
        else:
            print("✓ 잔존 미링크 0 — 검증된 인용은 모두 링크됨.")


if __name__ == "__main__":
    main()
