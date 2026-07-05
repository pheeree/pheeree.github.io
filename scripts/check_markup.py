#!/usr/bin/env python3
"""마크업 함정 검사 — formatting.md "빠른 자기 점검"의 기계판 (비차단).

kramdown은 수식 스팬보다 줄 구조(표)를 먼저 파싱한다. 그래서 인라인 수식
`$$...$$` 안이라도 이스케이프 안 된 `|`가 있으면 그 단락이 표로 깨진다
(2026-07-01 글 실측). mermaid v10의 점선 라벨 결합 실수(`-.- "라벨" .->`)도
파스 에러를 낸다(2026-07-02 글 실측). 또 한 다이어그램에 subgraph가 2개 이상이면
좁은 본문 컬럼(660px)에서 좌우로 짜부된다(2026-07-04 AutoMem 글 실측 — 05-13
레이아웃 점검이 확립한 "비교 subgraph는 별도 블록으로" 규약의 기계 승격). WARN.
이런 결정론적 함정만 잡는다. exit 0 고정 — 보고만 하고 판단은 저자의 몫.

사용: check_markup.py <글.md> [글2.md ...]
"""
import re
import sys
from pathlib import Path

UNESCAPED_PIPE = re.compile(r"(?<!\\)\|")
LATEX_PAREN = re.compile(r"\\[()]")
CURRENCY = re.compile(r"(?<![\\$\w])\$\d")
GREEK = re.compile(r"[α-ωΑ-Ω]")
MERMAID_DOTTED_COMPOUND = re.compile(r"-\.-+\s*\"")  # -.- "라벨" .-> 꼴
MERMAID_LABEL_NOSPACE = re.compile(r"(?:--|==|-\.)\"")  # 라벨 앞 공백 누락
MERMAID_SUBGRAPH = re.compile(r"^\s*subgraph\b")  # 한 다이어그램에 2개+면 좁은 컬럼에서 짜부


def check(md_path: Path) -> list[str]:
    findings = []
    text = md_path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            offset = parts[0].count("\n") + parts[1].count("\n") + 2
            text = parts[2]
        else:
            offset = 0
    else:
        offset = 0

    fence = None  # None | "mermaid" | "code"
    mermaid_start = 0
    mermaid_subgraphs = 0
    in_display_math = False
    for i, line in enumerate(text.splitlines(), start=offset + 1):
        stripped = line.strip()

        if stripped.startswith("```"):
            if fence is None:
                fence = "mermaid" if stripped[3:].strip().startswith("mermaid") else "code"
                if fence == "mermaid":
                    mermaid_start = i
                    mermaid_subgraphs = 0
            else:
                if fence == "mermaid" and mermaid_subgraphs >= 2:
                    findings.append(
                        f"{mermaid_start}: [WARN] mermaid 한 다이어그램에 subgraph {mermaid_subgraphs}개 — "
                        f"좁은 본문 컬럼(660px)에서 짜부된다. 비교용이면 별도 블록 여러 개로 분리, "
                        f'통합 구조면 방향을 TB로 (formatting.md "Mermaid")'
                    )
                fence = None
            continue

        if fence == "mermaid":
            if MERMAID_SUBGRAPH.search(line):
                mermaid_subgraphs += 1
            if MERMAID_DOTTED_COMPOUND.search(line):
                findings.append(f'{i}: [ERROR] mermaid 점선 결합 `-.- "라벨" .->` — 정확형은 `-. "라벨" .->`')
            if MERMAID_LABEL_NOSPACE.search(line):
                findings.append(f'{i}: [ERROR] mermaid edge 라벨 앞 공백 누락 — `-- "라벨" -->` 꼴로')
            continue
        if fence == "code":
            continue

        # 디스플레이 수식($$ 단독 줄 토글, 또는 한 줄짜리 $$…$$ 블록)은 kramdown이 보호한다
        if stripped == "$$":
            in_display_math = not in_display_math
            continue
        if in_display_math:
            continue
        if stripped.startswith("$$") and stripped.endswith("$$") and len(stripped) > 4:
            continue

        # 표 행·IAL(kramdown 지시자)은 정상 사용
        if stripped.startswith(("|", "{:")):
            continue

        if UNESCAPED_PIPE.search(line):
            findings.append(
                f"{i}: [ERROR] 프로즈 줄의 이스케이프 안 된 `|` — kramdown 표 오인으로 단락이 깨진다. "
                f"조건부 막대는 `\\mid`, 절댓값 `\\lvert`, norm `\\lVert`, 아니면 별도 줄 디스플레이 블록으로"
            )
        if LATEX_PAREN.search(line):
            findings.append(f"{i}: [ERROR] `\\(`·`\\)` 잔재 — kramdown이 escape해 MathJax가 못 찾는다. `$$...$$`로")
        if CURRENCY.search(line):
            findings.append(f"{i}: [WARN] 통화 `$숫자` — `\\$`로 이스케이프 (MathJax 트리거 충돌)")
        if GREEK.search(line) and "$" not in line:
            findings.append(f"{i}: [WARN] 수식 밖 그리스 문자 노출 — `$$...$$`로 감싸기")
    return findings


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        return
    total = 0
    for arg in sys.argv[1:]:
        path = Path(arg)
        findings = check(path)
        total += len(findings)
        if findings:
            print(f"═══ {path.name} — {len(findings)}건")
            for f in findings:
                print(f"  {f}")
    if total == 0:
        print("[markup] 함정 없음 ✓")


if __name__ == "__main__":
    main()
