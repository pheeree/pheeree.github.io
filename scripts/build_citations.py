#!/Users/pheeree/miniconda3/bin/python3
"""블로그 포스트의 서지정보 + 원문 링크를 모아 _data/citations.yml 로 빌드.

산출:
  _data/citations.yml   — 글별 서지(중심 논문 + 본문 인용), 기계 판독용 단일 출처
  bibliography.md       — citations.yml 을 사람이 읽게 렌더한 페이지

옵션:
  python scripts/build_citations.py              # citations.yml + bibliography.md 생성
  python scripts/build_citations.py --link-posts # 위 + 본문 평문 arXiv를 검증된 것만 하이퍼링크화
  python scripts/build_citations.py --check       # 생성하지 않고 통계만

검증 정책 (죽은 링크 0):
  - arXiv id 는 arxiv-cache(우리 PDF 보유) 우선 → 실재 확정.
  - cache 에 없는 id 는 arXiv API 배치 조회로 실재+메타 확인. 응답에 없으면 죽은 id → 링크 안 함.
  - --link-posts 는 검증된 id 만 본문 링크화. 각주(`[^`)·코드블록·이미 링크된 것은 건드리지 않는다.

설계:
  - 블로그 레포 자기완결. KM 미러의 arxiv-cache 는 읽되 없으면 건너뜀(선택적 의존).
  - arXiv fetch 로직은 작게 내장(KM arxiv_enrich.py 의 fetch_batch 와 같은 형태).
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

ARXIV_ID = re.compile(r"\b(\d{4}\.\d{4,5})(v\d+)?\b")
ARXIV_MENTION = re.compile(r"arXiv:(\d{4}\.\d{4,5})(v\d+)?", re.IGNORECASE)
SOURCE_LINE = re.compile(r'^source:\s*["\']?PAPER/(\d{4}\.\d{4,5})', re.MULTILINE)
FM_TITLE = re.compile(r'^title:\s*["\']?(.+?)["\']?\s*$', re.MULTILINE)

USER_AGENT = "pheeree-blog/1.0 (mailto:pheeree@gmail.com)"
RETRY_MAX = 3
RETRY_BACKOFF = (30, 60, 120)
NS = {"a": "http://www.w3.org/2005/Atom"}


# ---------- arXiv 조회 ----------

def load_mirror_cache() -> dict:
    if not MIRROR_CACHE.exists():
        return {}
    try:
        return json.loads(MIRROR_CACHE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def fetch_batch(ids: list[str]) -> dict[str, dict]:
    """arXiv API 배치 조회. 반환 dict 에 없는 id = 죽은(존재 안 함) id."""
    if not ids:
        return {}
    q = urllib.parse.urlencode({"id_list": ",".join(ids), "max_results": len(ids)})
    url = f"http://export.arxiv.org/api/query?{q}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_exc = None
    for attempt in range(RETRY_MAX):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read().decode("utf-8")
            break
        except urllib.error.HTTPError as e:
            last_exc = e
            if e.code != 429 or attempt == RETRY_MAX - 1:
                raise
            time.sleep(RETRY_BACKOFF[attempt])
        except (TimeoutError, urllib.error.URLError) as e:
            last_exc = e
            if attempt == RETRY_MAX - 1:
                raise
            time.sleep(RETRY_BACKOFF[attempt])
    else:
        raise last_exc or RuntimeError("재시도 루프 비정상 종료")

    out = {}
    root = ET.fromstring(data)
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
        out[base_id] = {
            "title": title,
            "authors": authors,
            "published": published,
        }
    return out


def resolve_ids(ids: set[str], cache: dict, do_fetch: bool) -> dict[str, dict]:
    """id → 메타. cache 우선, 없으면 (do_fetch 시) API. 응답 없는 id 는 제외(죽은 링크)."""
    resolved = {}
    missing = []
    for i in ids:
        entry = cache.get(i)
        if entry and not entry.get("not_found"):
            resolved[i] = {
                "title": entry.get("title", ""),
                "authors": entry.get("authors", []),
                "published": entry.get("published", ""),
            }
        else:
            missing.append(i)

    if do_fetch and missing:
        # arXiv API 배치 한도 고려해 50개씩.
        for k in range(0, len(missing), 50):
            chunk = missing[k:k + 50]
            try:
                got = fetch_batch(chunk)
            except Exception as e:
                print(f"    · API 조회 실패 (이 묶음 평문 유지): {e}", file=sys.stderr)
                got = {}
            resolved.update(got)
            if k + 50 < len(missing):
                time.sleep(3)  # arXiv 예의상 간격
    return resolved


# ---------- 포스트 파싱 ----------

def post_slug(path: Path) -> str:
    return path.stem


def collect_ids_from_post(text: str) -> tuple[str | None, set[str]]:
    """(중심 논문 id 또는 None, 본문 등장 모든 id set)."""
    central = None
    m = SOURCE_LINE.search(text)
    if m:
        central = m.group(1)
    body_ids = {m.group(1) for m in ARXIV_MENTION.finditer(text)}
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
            lines.append(f'    url: "{c["url"]}"')
        refs = pm.get("referenced", [])
        if refs:
            lines.append("  referenced:")
            for r in refs:
                title = f', title: "{yaml_escape(r["title"])}"' if r.get("title") else ""
                lines.append(f'    - {{ id: "{r["id"]}"{title}, url: "{r["url"]}" }}')
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
            lines.append(f"- **중심**: {who}*{c['title']}*. [arXiv:{c['id']}]({c['url']})")
        for r in pm.get("referenced", []):
            t = f"*{r['title']}*. " if r.get("title") else ""
            lines.append(f"- {t}[arXiv:{r['id']}]({r['url']})")
        lines.append("")
    return "\n".join(lines)


# ---------- 본문 링크화 ----------

def link_post_body(text: str, valid_ids: set[str]) -> tuple[str, int]:
    """본문의 평문 `arXiv:ID` 를 검증된 id 만 하이퍼링크화.
    각주 정의 줄(`[^`)·코드블록·이미 링크 안에 있는 것은 제외."""
    lines = text.split("\n")
    in_fence = False
    changed = 0
    for idx, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("[^"):  # 각주 정의 줄은 보수적으로 건너뜀
            continue

        def repl(m):
            nonlocal changed
            base = m.group(1)
            ver = m.group(2) or ""
            if base not in valid_ids:
                return m.group(0)
            # 직전이 `[` 면 이미 링크 텍스트(`[arXiv:..](url)`)이므로 건드리지 않는다.
            # 단순히 뒤가 `)`인 경우(예: 평문 `(arXiv:1234.5678)`)는 보호 아님 — 링크 대상.
            start = m.start()
            if start > 0 and line[start - 1] == "[":
                return m.group(0)
            changed += 1
            return f"[arXiv:{base}{ver}](https://arxiv.org/abs/{base})"

        lines[idx] = ARXIV_MENTION.sub(repl, line)
    return "\n".join(lines), changed


# ---------- main ----------

def main() -> None:
    check_only = "--check" in sys.argv
    link_posts = "--link-posts" in sys.argv

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

    # id 해소 (cache + API)
    do_fetch = not check_only or "--check" in sys.argv  # check 에서도 커버리지 보려면 fetch
    resolved = resolve_ids(all_ids, cache, do_fetch=not check_only)

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
                "url": f"https://arxiv.org/abs/{cid}",
            }
        refs = []
        for i in sorted(pp["ids"]):
            if i == cid:
                continue
            if i in resolved:
                refs.append({
                    "id": i, "title": resolved[i]["title"],
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
        for pp in parsed:
            new_text, n = link_post_body(pp["text"], valid_ids)
            if n > 0:
                pp["path"].write_text(new_text, encoding="utf-8")
                linked_posts += 1
                linked_total += n
        print(f"본문 링크화: {linked_posts}편에서 {linked_total}개 평문 arXiv → 하이퍼링크")


if __name__ == "__main__":
    main()
