#!/usr/bin/env python3
"""드래프트의 영어 따옴표 인용을 원문 텍스트와 글자 단위로 대조한다 (비차단 점검).

왜 (2026-10-01 신설):
    신뢰 장부(claim-check)와 기존 점검 스크립트(arXiv id 실재·마크업·문장 재사용·
    무게 점검) 어느 것도 "따옴표 안의 문장이 원문과 한 글자도 다르지 않은가"를 보지
    않는다. 09-29 글의 각주 하나가 원문의 "We hope that our work ..."를 "that" 없이
    소문자로 옮긴 채 발행됐고, 이 대조를 처음 돌렸을 때 걸렸다.

방법:
    - 드래프트에서 따옴표(" ")로 감싼 영문 18자 이상 구간을 모두 뽑는다(한글 위주 구간 제외).
    - 알파벳·숫자만 남겨 원문 코퍼스의 합집합에서 찾는다 — 줄바꿈 하이픈·곡선 따옴표·
      특수 마이너스 차이는 흡수. 생략 표시(…, ...)로 이은 인용은 조각별로 대조.
    - 코퍼스가 없는 인용(2차 출처·논문 제목)은 MISS로 나온다 — 그 자체가 "원문 미대조"의
      신호이고, 따옴표를 쓰지 말라는 규칙을 어겼는지 사람이 본다.

사용:
    pdftotext 논문.pdf 논문.txt                # 코퍼스는 pdftotext(레이아웃 옵션 없이) 또는 arXiv HTML 텍스트
    verify_quotes.py <드래프트.md> 논문1.txt [논문2.txt ...]

한계: 영문 인용만 본다. 번역·의역은 대상이 아니다. 줄 시작이 `>`인 블록 인용은 따옴표가 없어
    잡지 못한다.
"""
import re
import sys


def alnum(s: str) -> str:
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    return re.sub(r"[^A-Za-z0-9]", "", s)


def is_english(s: str) -> bool:
    letters = re.findall(r"[A-Za-z]", s)
    hangul = re.findall(r"[가-힣]", s)
    return len(letters) >= 12 and len(hangul) <= 2


def main() -> int:
    draft = open(sys.argv[1], encoding="utf-8").read()
    corpus = ""
    for p in sys.argv[2:]:
        corpus += open(p, encoding="utf-8").read() + "\n"
    C = alnum(corpus)
    # 곡선 따옴표를 직선으로 통일한 뒤 추출
    d = draft.replace("“", '"').replace("”", '"')
    quotes = re.findall(r'"([^"\n]{18,}?)"', d)
    miss = 0
    n = 0
    seen = set()
    for q in quotes:
        if q in seen or not is_english(q):
            continue
        seen.add(q)
        n += 1
        # 생략 표시(…, ..., […])로 이어 붙인 인용은 조각별로 대조
        parts = [x for x in re.split(r"\s*(?:…|\.\.\.|\[\.\.\.\]|\[…\])\s*", q) if len(alnum(x)) >= 12]
        ok = all(alnum(x) in C for x in parts)
        if not ok:
            miss += 1
        print(("OK   " if ok else "MISS ") + q[:150])
    print(f"\n영문 인용 {n}개 중 MISS {miss}개")
    return 1 if miss else 0


if __name__ == "__main__":
    sys.exit(main())
