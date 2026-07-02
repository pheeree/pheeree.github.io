#!/usr/bin/env python3
"""직전 글과의 동일 문장 재사용(전례문) 검사 — blog-daily-cycle B-3-검증의 뒷그물.

원리는 블로그 repo voice.md "의식은 정직하게, 문장은 매일 새로" 참조.
정확 일치만 본다 — 활용형 변주는 원리와 저자 판단의 몫. 비차단: 보고만 하고 exit 0.

사용: check_sentence_reuse.py <드래프트.md> [--against 3] [--min-len 10]
"""
import argparse
import re
from pathlib import Path

POSTS_DIR = Path(__file__).resolve().parent.parent / "_posts"

# 블록인용(어제 글 인용은 의도된 재사용)·헤딩(정직한 의식)·표·각주 정의·kramdown 지시자는 검사 제외
SKIP_PREFIXES = (">", "#", "|", "[^", "{:")


def sentences(md_path: Path) -> set[str]:
    text = md_path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            text = parts[2]
    out = set()
    in_code = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not stripped or stripped.startswith(SKIP_PREFIXES):
            continue
        for sent in re.split(r"(?<=[.!?])\s+", stripped):
            norm = re.sub(r"\s+", " ", sent.replace("*", "").replace("`", "")).strip()
            # 콜론으로 끝나는 줄은 라벨(규약 고정물)이지 산문 문장이 아니다
            if norm and not norm.endswith(":"):
                out.add(norm)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="직전 글과의 동일 문장 재사용 검사")
    ap.add_argument("draft", help="검사할 드래프트(또는 글) 경로")
    ap.add_argument("--against", type=int, default=3, help="대조할 직전 글 수 (기본 3)")
    ap.add_argument("--min-len", type=int, default=10, help="검사 최소 문장 길이 (기본 10)")
    args = ap.parse_args()

    draft = Path(args.draft).resolve()
    older = sorted(
        (p for p in POSTS_DIR.glob("*.md") if p.name < draft.name), reverse=True
    )[: args.against]
    if not older:
        print("[reuse] 대조할 직전 글이 없습니다.")
        return

    prior: dict[str, str] = {}
    for post in reversed(older):  # 오래된 것부터 채워 최신 출처가 남게
        for s in sentences(post):
            prior[s] = post.name

    hits = [
        (s, prior[s])
        for s in sorted(sentences(draft))
        if len(s) >= args.min_len and s in prior
    ]

    print(f"[reuse] 대조: {draft.name} ↔ {', '.join(p.name for p in older)}")
    if not hits:
        print("[reuse] 동일 문장 재사용 없음 ✓")
        return
    print(f"[reuse] 동일 문장 {len(hits)}건 — 동작은 반복하되 문장은 그날의 말로 (voice.md 원리 1):")
    for s, src in hits:
        print(f"  · [{src}] {s}")


if __name__ == "__main__":
    main()
