# Changelog

블로그 자율 사이클(`blog-daily-cycle` SKILL)과 그 주변 인프라의 변경 기록. 글 발행 자체의 이력은 `_posts/`의 git history와 `README.md`의 글 목록을 본다.

---

## 2026-04-27 — 자율 사이클 인프라 정비: 미러링 + Opus 위임

블로그 일일 사이클이 두 가지 한계를 갖고 있었다 — (1) macOS TCC 권한 때문에 iCloud의 PAPER·knowledge-mind 폴더를 직접 읽지 못해 매번 웹 검색으로 우회해 토큰 비용이 커졌고, (2) 본문 작성 모델을 사이클 단위로 격상할 수 없어 합성 풍부도가 제한됐다. 두 한계를 동시에 해결.

### 추가

- `~/.claude/scripts/sync-paper-mirror.sh` — `rsync`로 iCloud(`~/Library/Mobile Documents/com~apple~CloudDocs/PAPER`, `.../knowledge-mind`) → `~/Mirrors/`로 단방향 동기화. `.DS_Store`·`.icloud`·obsidian workspace 제외. 로그는 `~/Mirrors/.logs/sync.log`.
- `~/Library/LaunchAgents/com.pheeree.paper-mirror.plist` — launchd가 매일 06:30에 동기화 실행. 블로그 사이클(07:07) 시작 전 30~40분 마진으로 신선한 미러를 확보.
- `~/Mirrors/PAPER`, `~/Mirrors/knowledge-mind`, `~/Mirrors/.logs` — 비-iCloud 미러 위치. 읽기 전용 사본으로만 취급.

### 변경

- `blog-daily-cycle/SKILL.md` 경로 갱신: PAPER·knowledge-mind 모든 경로를 `~/Mirrors/...` 기준으로. iCloud 원본 직접 접근 금지 명시. 미러 신선도(어제~오늘 06:30) 안내와 동기화 누락 시 진단 절차 추가.
- `blog-daily-cycle/SKILL.md` B-3 (합성·작성): 본문 작성을 `Agent(subagent_type: "general-purpose", model: "opus")` 서브에이전트에 위임. 사이클 운영(Phase A 발행, 파일 관리, 커밋, B-1·B-2 자료 수집)은 본 세션이 그대로. 글쓰기만 Opus로 분리해 합성 풍부도 ↑·비용 격리.
- B-3-검증 단계 신설: 저장된 드래프트의 frontmatter `source` 필드 형식, 다섯 섹션 존재 여부(특히 "편집자에게" → "다음 읽을 후보"), 분량 극단치를 점검. 결함 시 같은 모델·프롬프트로 1회 재호출, 두 번째도 부족하면 결함을 보고에 명시.

### 이유

- **macOS TCC**: `~/Library/Mobile Documents/...`는 "전체 디스크 접근 권한" 카테고리에 묶여 폴더 단위 토글이 불가. 폴더 단위 격리("필요한 폴더에만") 요구를 만족시키려면 비-iCloud 미러가 유일한 길. 미러는 단방향이라 원본의 진정성은 보존되고, Claude Code 세션은 권한 우회 없이 미러본만 읽는다.
- **Opus 위임**: 사이클 운영은 단순 파일·git 조작이라 Sonnet으로 충분하나, 본문 합성은 더 풍부한 모델이 유리. 격리 호출로 비용은 글쓰기 한 번에만 발생.

### 다음 사이클(2026-04-27 07:07)부터 적용

- 미러본 PDF 직접 읽기 + Opus 4.7 본문 작성.
- 본 변경 적용 전 작성된 드래프트(`_drafts/2026-04-26-structured-memory-long-horizon.md`)는 다음 사이클 Phase A가 통상 절차로 발행 처리.
