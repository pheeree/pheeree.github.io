#!/usr/bin/env python3
"""신뢰 장부에서 △(원문 미대조)로 표시된 주장이 본문 논증의 전제로 쓰였는지 본다.

왜 (2026-08-29 신설):
    claim-check의 신뢰 장부는 "대조했는가"를 묻지만 "본문이 그 미대조 주장에
    얼마나 기대고 있는가"는 묻지 않는다. 2026-08-29 재귀 추론기 압축 편에서
    △로 표시된 "ETH가 나이브 INT4 QAT를 0.0→71.8%로 복구"가 중심 논문 주장 3을
    반박하는 논증 전체를 떠받쳤고, 원문 대조 결과 사실과 달랐다(ETH는 QAT를
    쓰지 않는다 — per-block 스케일링으로 재훈련 없이 복구). 각주에는 정확한
    내용이 이미 적혀 있었으나 본문이 그와 어긋난 채 논증을 세웠다.

    표시는 정직했는데 무게가 과했다. 이 스크립트는 그 무게를 잰다.

한계:
    휴리스틱이다. 정밀도보다 재현율을 택했다 — 놓치는 것보다 시끄러운 편이 낫다.
    비차단이며, 판정은 읽는 쪽의 일이다.

사용:
    python3 check_claim_load.py <파일...>
"""
import re
import sys

# 장부 행: | 주장 | 출처 | 상태 |
LEDGER_ROW = re.compile(r"^\|\s*(?P<claim>[^|]+?)\s*\|\s*(?P<src>[^|]+?)\s*\|\s*(?P<st>[△⚠✓?])\s*\|\s*$", re.M)

# 논증에 무게가 실린 자리를 가리키는 표지
LOAD_MARKERS = [
    "그러나", "하지만", "반면", "반례", "부딪", "충돌", "뒤집", "아프",
    "반박", "정면", "논쟁", "무너", "막혀", "틀렸", "어긋",
    "따라서", "그러니", "때문에", "근거", "기준선",
]

SECTION = re.compile(r"^##\s+(.+)$", re.M)


def body_of(text):
    """frontmatter·각주 정의·장부 표·코드블록을 걷어낸 본문."""
    if text.startswith("---"):
        text = text.split("---", 2)[-1]
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"^\[\^[^\]]+\]:.*(?:\n(?![\[\n]).*)*$", "", text, flags=re.M)
    text = re.sub(r"^\|.*$", "", text, flags=re.M)
    return text


def tokens_of(claim):
    """주장의 식별 토큰.

    **소수점 수치만 발화 조건으로 삼는다.** 이 실패의 형태는 측정값이 뒤틀려
    옮겨지는 것이고(2026-08-29: 중심 논문의 71.9가 ETH의 71.8로), 그런 값은
    거의 언제나 소수다. 맨정수(14·100)와 라틴 약어(CKA·LLM)는 흔해서
    오탐만 만든다 — 근거로 함께 보여 주되 발화시키지는 않는다.
    """
    decimals = [d for d in re.findall(r"\d+\.\d+", claim) if d != "0"]
    support = re.findall(r"\b[A-Z][A-Za-z0-9]{2,}\b", claim)
    return decimals, support


def check(path):
    text = open(path, encoding="utf-8").read()
    rows = [m for m in LEDGER_ROW.finditer(text)
            if m.group("st") in "△⚠" and "주장" not in m.group("claim")]
    if not rows:
        return []

    body = body_of(text)
    paras = [p for p in re.split(r"\n\s*\n", body) if p.strip()]
    findings = []

    for m in rows:
        claim = m.group("claim")
        decimals, support = tokens_of(claim)
        if not decimals:
            continue
        for para in paras:
            hit = [t for t in decimals if t in para]
            if not hit:
                continue
            hit += [t for t in support if t in para]
            marks = [k for k in LOAD_MARKERS if k in para]
            if not marks:
                continue
            head = re.sub(r"\s+", " ", para.strip())[:110]
            findings.append({
                "claim": re.sub(r"\s+", " ", claim)[:90],
                "status": m.group("st"),
                "tokens": hit,
                "markers": marks[:3],
                "excerpt": head,
            })
            break  # 주장당 한 번만
    return findings


def main(paths):
    total = 0
    for path in paths:
        found = check(path)
        name = path.split("/")[-1]
        if not found:
            print(f"[claim-load] {name} — 미대조 주장이 논증을 떠받치는 자리 없음 ✓")
            continue
        print(f"═══ {name} — {len(found)}건")
        for f in found:
            total += 1
            print(f"  [{f['status']}] {f['claim']}")
            print(f"      토큰 {f['tokens']} · 표지 {f['markers']}")
            print(f"      → {f['excerpt']}…")
        print("  이 주장들은 원문 미대조인데 본문이 논증의 무게를 실었다.")
        print("  발행 전 원문을 대조하거나, 본문에서 무게를 덜어낼 것.")
    return 1 if total else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))
