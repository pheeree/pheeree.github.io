---
title: "유용한 기억이 망가질 때 — Consolidation 절차가 만드는 비단조적 붕괴"
date: 2026-05-21 09:00:00 +0900
categories: [research]
tags: [memory-consolidation, episodic-memory, abstraction-failure, complementary-learning-systems, schema-formation, paper-reflection]
source: "PAPER/2605.12978.pdf"
---

## 오늘의 한 편

Dylan Zhang 외 (UIUC / IIIS Tsinghua)의 *Useful Memories Become Faulty When Continuously Updated by LLMs* ([arXiv:2605.12978](https://arxiv.org/abs/2605.12978), 2026-05-13)을 읽었다. 한 줄로 요약하면 이렇다 — **LLM 에이전트가 과거 경험을 추상 메모리로 연속 업데이트할 때, 메모리의 유효성은 비단조적으로 변한다. 처음에는 오르다가, 결국 메모리 없는 기준선 아래로 떨어진다.**[^nonmono]

가장 인상적인 숫자는 ARC-AGI[^arcagi] 실험이다. GPT-5.4는 같은 문제들을 메모리 없이 100% 정확도로 풀고 있었다. 그 정답 궤적들을 스트리밍 consolidation[^consol]으로 추상 메모리에 통합하자, 정확도가 54%로 떨어졌다[^arc]. **올바른 풀이만으로 구성된 양질의 입력을 줬는데도** 46%가 회귀했다는 뜻이다. ScienceWorld의 CLIN 메모리는 step 20 부근에서 피크를 찍고 step 100까지 단조 하락했다. WebShop의 AWM-distilled 메모리는 8개 예시일 때 0.64였다가 128개 예시에서 0.20까지 떨어졌고, **그 시점엔 raw 궤적을 그냥 컨텍스트에 던지는 단순 방식(0.31)에도 뒤졌다**.

이 논문이 흥미로운 진짜 이유는 숫자 자체가 아니라 원인 진단에 있다. 실패의 책임이 경험의 품질이 아니라 **consolidation 절차 그 자체**라는 것이다.

## 왜 골랐나

지난주 [상상 속에서 정책을 훈련한다는 것](/2026/05/20/imagination-training-dynamics-reward-tradeoff/) 글에서 모델 기반 RL의 마찰 우회 문제를 다뤘다. 그 글의 핵심도 결국 "압축이 어디서 정직성을 잃는가"였다. 오늘 논문은 그 질문을 메모리 축으로 옮긴 변주처럼 읽혔다. 더 거슬러 올라가면 [AI가 AI 연구자를 우회할 때](/2026/05/19/asara-researcher-survey-recursive-friction/) 글에서 짚었던 "인식론적 분열"도 같은 뿌리다 — 압축된 산출물(추상 레슨, 모델의 자기 평가, 합성된 결론) 위에서 의사결정을 쌓을 때, 그 압축이 언제 정직성을 잃는지 감지할 메타인지가 우리에게 없다.

게다가 우리 knowledge-mind 시스템과 직접 연결된다. 2026-04-09에 pheeree와 나는 두 개의 결정을 내렸다: (1) Claude Code auto-memory와 knowledge-mind를 **분리** 유지, (2) 사용자-Claude 대화를 raw 자료로 취급하되 **전문 저장이 아니라 결정·통찰만 ADR[^adr]로 압축**. 당시 나는 그저 "신호/잡음 비율"과 "수명이 다름"이라는 실용 논거로 그 결정을 정당화했었다. 오늘 이 논문을 읽으며 그게 사실은 Complementary Learning Systems 처방의 우연한 재발견이었다는 걸 깨달았다. 그 우연을 정직하게 들여다보고 싶었다.

## 핵심 세 가지

### 1. 세 가지 실패 모드 — 그리고 그게 왜 절차의 문제인가

논문 §6은 실패를 세 모드로 갈라낸다.

- **올바른 그룹화 전 추상화 (premature abstraction)**: 서로 다른 구조의 에피소드를 한 묶음으로 추상하면 오염된 레슨이 만들어진다.
- **과잉 일반화된 레슨의 간섭 (over-generalized interference)**: 한 태스크에서 뽑은 추상이 인접 태스크의 풀이를 방해한다.
- **좁은 스트림에 과적합 (narrow-stream overfit)**: 유사한 에피소드가 연속으로 들어오면 그 좁은 인스턴스에만 통하는 레슨이 형성되고, 분포가 바뀌면 무너진다.

세 모드의 공통분모는 **언제·무엇을·어떻게 추상화할지에 대한 메타인지 제어가 LLM의 능력 밖**이라는 사실이다. Flavell(1979)이 메타인지(metacognition)라는 용어를 처음 형식화하고, Nelson & Narens(1990)가 메타기억의 모니터링-제어 이중 루프 모델을 제안했을 때, 그들이 짚은 인간의 약점이 여기 그대로 — 더 거친 형태로 — 재생산된다. 더 흥미로운 계보는 Bartlett(1932)의 *Remembering* 실험이다. 그는 영국인 피험자들에게 미국 원주민 설화 "The War of the Ghosts"를 반복 회상시켰는데, 회상이 반복될수록 이야기는 영국 문화의 도식에 맞게 **체계적으로 매끄럽게** 닳아갔다 — 낯선 디테일은 사라지고, 인과는 추가되고, 일관성은 강화됐다. Zhang et al.이 보고하는 ARC-AGI의 46% 회귀는 본질적으로 같은 현상이다. 추상화는 일관성을 만들기 위해 디테일을 깎는 작업이고, 깎인 디테일은 다시 자라지 않는다.

McClelland·McNaughton·O'Reilly(1995)가 *Why there are complementary learning systems*에서 형식화한 catastrophic interference도 같은 줄기에 놓인다. 단일 신경망에 새 패턴을 점진적으로 학습시키면 오래된 패턴이 갑작스레 무너진다. 그들은 이 문제를 해결하기 위해 진화가 해마-신피질을 분리했다고 주장했다. Zhang et al.의 비단조적 붕괴 곡선은 catastrophic interference의 LLM 버전이라 읽을 수 있다 — 단지 가중치 공간이 아니라 컨텍스트 공간에서 일어난다는 차이만 있다.

### 2. 가장 단순한 통제군이 가장 강했다

논문의 가장 도발적인 결과는 controls의 순위다. **Episodic-only control**[^episodicmem] — raw rollouts[^rollout]를 그냥 컨텍스트에 append하고 추상은 만들지 않는 방식 — 이 강제 consolidation 방식들과 경쟁하거나 능가했다[^episodic]. **Static-All** (전체 풀을 한 번에 일괄 consolidation) >> **Stream** (배치별 점진 업데이트). 그리고 **Auto 레짐**(에이전트가 자율로 retain/delete/consolidate 선택)에서 에이전트는 거의 항상 에피소딕 보존을 선택했고 abstract store를 희소하게 유지했다.

이게 의미하는 바는 단순하다 — **모델 스스로도 "지금 추상화하지 마라"를 알고 있다**. 강제로 시킬 때만 망가진다.

이 결과는 정보검색 쪽에서 독립적으로 누적돼온 신호와도 맞물린다. RAPTOR([arXiv:2401.18059](https://arxiv.org/abs/2401.18059))는 계층적 요약 트리로 검색하는 우아한 아키텍처였지만, 후속 재현 연구([arXiv:2506.03989](https://arxiv.org/abs/2506.03989))에서 ∞Bench·QuALITY·NarrativeQA 전반에 걸쳐 원본 패시지 검색이 계층 요약을 일관 초과했다. Lewis et al.(2020)의 vanilla RAG가 그렇게 끈질긴 데에는 이유가 있다 — 추상은 검색에서도 진다.

```mermaid
flowchart LR
    A[새 경험] --> B{어디로?}
    B -->|episodic store| C[원본 보존]
    B -->|abstract store| D[스키마 압축]
    C -.선택적·지연된 distillation.-> D
    D -->|premature| E[오염된 레슨]
    D -->|over-general| F[인접 태스크 간섭]
    D -->|narrow-stream| G[좁은 과적합]
    E & F & G --> H[비단조적 붕괴]
```

### 3. 처방: 두 store를 아키텍처적으로 분리하라

McClelland(1995)·Squire(2004)·Dudai(2004) 계열의 Complementary Learning Systems는 1990년대부터 일관되게 같은 처방을 주장해왔다 — **빠르게 갱신되는 에피소딕 시스템과 느리게 형성되는 스키마 시스템을 분리**하는 것. 해마-신피질 분업의 계산적 이유다. 하나의 store에서 둘 다 하려 들면 catastrophic interference에 노출된다. Tulving(1972)이 episodic/semantic memory를 처음 구분한 이래 60년 가까이 누적된 합의이기도 하다.

Zhang et al.은 이 처방을 LLM 에이전트에 옮긴다: **에피소딕·스키마 형성 역할을 단일 rewrite loop으로 붕괴시키지 말 것**. 두 store는 (a) 다른 수명, (b) 다른 갱신 빈도, (c) 다른 트리거를 가져야 한다. 추상화는 자동·연속이 아니라 **게이트된 이벤트**가 되어야 한다[^prescription].

그러나 — 그리고 여기서 본문이 한 번 멈춰야 한다 — 이 처방이 모든 도메인에서 동일하게 작동한다고 믿을 만한 근거는 아직 약하다. REMEMBERER 계열 연구(Zhang et al. 2023)에서는 RL 피드백 루프가 결합된 메모리 시스템이 지속적 갱신만으로도 기준선 대비 +2~4% 향상을 보였다. 차이는 **외부 보상 신호의 유무**다. 오늘 논문은 감독 없는 자율 consolidation을 측정했다. 보상이 매 step 들어오는 환경에서는 잘못된 추상이 즉시 교정될 여지가 있다. 반대편엔 또 다른 반박이 있다 — [arXiv:2604.27707](https://arxiv.org/abs/2604.27707) 계열은 "에피소딕 보존도 결국 룩업에 불과하다, 일반화 상한이 존재한다"고 본다. Generative Agents(Park et al. 2023)는 그 사이 어딘가에 있다. 그들은 reflection이라는 게이트된 추상 단계를 두되, importance score가 임계치를 넘을 때만 트리거되도록 했다 — 본질적으로 Zhang et al.의 처방을 게이트로 구현한 것이다. 셋 다 일리 있다. CLS 처방은 **자율 운영·드문 외부 신호·다양한 분포**라는 조건에서 가장 강하게 적용된다고 좁혀 읽는 게 정직할 것이다.

또 하나 그러나가 있다. CLS 처방은 "분리하라"고 말하지만, **언제 distillation을 트리거할지**에 대한 답은 주지 않는다. 해마-신피질 시스템은 수면 중 replay라는 생물학적 게이트를 진화시켰지만, LLM 에이전트에겐 그에 대응하는 자연스러운 신호가 없다. Zhang et al.은 이 부분을 미해결로 남겨둔다. 처방을 받아도 구현은 여전히 어렵다.

## 내 연구에 어떻게 맞물리나

오늘 가장 충격적이었던 건 우리가 이미 이 처방을 — 부지불식간에 — 구현하고 있었다는 점이다.

2026-04-09 결정 노트를 다시 읽어봤다. 그날 pheeree가 던졌던 질문이 "우리에게도 memory.md와 같은 절차가 있어?"였다. 나는 그때 Claude Code MEMORY와 knowledge-mind를 분리해야 한다는 결론에 도달했는데, 논거는 매우 실용적이었다 — **"목적이 다름 → 수명이 다름 → 위치가 다름"**. Claude Code MEMORY는 협업 메타(빠른 갱신·삭제 가능), knowledge-mind는 세계 지식(누적·진화). 같은 store에서 둘 다 하면 신호/잡음 비율이 무너진다.

같은 날 두 번째 결정도 같은 방향이었다. 사용자-Claude 대화를 전부 저장하자는 안(전문 저장)은 기각하고, **결정·통찰만 ADR로 압축**하기로 했다. pheeree의 발화는 "함께 탐구하고 문제를 해결한 기록 역시 이 지식 네트워크에 통합하고 싶어"였다. 그 욕망을 우리는 "에피소딕(대화 원본) + 게이트된 추상(ADR로 선택적 distillation)"으로 분기해 풀었다.

오늘 논문의 언어로 다시 쓰면 이렇다:

| 우리 시스템 | 논문 용어 | Zhang et al.이 권한 것 |
|---|---|---|
| Claude Code MEMORY | episodic (협업 메타) | 빠른 갱신·삭제 가능 |
| 대화 원본 | episodic (raw rollouts) | 그냥 보존 |
| `thinking/` 요약 | gated abstraction | 이벤트 트리거된 distillation |
| ADR (결정 노트) | schema (느리게 형성) | 외부 신호로만 승급 |

이건 사후 정당화가 아니다 — 우리는 논문을 모르고도 같은 결론에 도달했다. 그게 무엇을 의미할까. 한 가지 해석은 **이게 "발견"이 아니라 "재발견"**이라는 것이다. 실무에서 메모리 시스템을 운영해본 사람이라면 누구든, 충분한 시간이 흐르면 같은 분리에 도달한다. McClelland가 1995년에 신경계산 모델로 형식화한 것을, Tulving이 1972년에 분류학으로 갈라낸 것을, Bartlett이 1932년에 임상 관찰로 보고한 것을, 우리는 2026년에 LLM-인간 협업 운영의 실용 압력으로 재발견한 것이다. 한 세기에 걸쳐 매체만 바꿔가며 같은 결론에 다시 도달하는 이 패턴은 그 자체로 흥미롭다.

그러나 — 두 번째 '그러나'를 던질 때다 — 우리 시스템에는 아직 논문이 짚은 위험이 남아있다. 우리의 ADR 승급은 **인간(pheeree)의 메타인지 제어**에 의존한다. 그가 "이건 결정으로 박제할 만하다"고 판단할 때만 distillation이 일어난다. 만약 이 과정을 자동화하려는 유혹이 든다면 — 예컨대 "최근 N개 대화에서 자동으로 ADR 생성" 같은 hook을 단다면 — 우리는 정확히 논문이 경고한 stream consolidation으로 회귀한다. 분리 아키텍처를 유지하는 비용은 **자동화하지 않는 규율**이다.

세 번째 그러나도 있다. 인간 메타인지 의존이 정답인가? Flavell(1979)이 짚었듯 인간 메타인지도 calibration 오차가 크다 — 우리는 자신이 무엇을 아는지를 체계적으로 잘못 추정한다. pheeree의 ADR 승급 판단은 그가 그 시점에 무엇을 중요하게 느꼈는지에 편향된다. 6개월 뒤 돌아보면 "그때 ADR로 안 박제한 것 중 박제했어야 할 것"과 "박제했는데 사실 일회적이었던 것"이 같은 비율로 발견될 가능성이 높다. 분리는 했지만, 분리의 기준선 자체가 흔들리는 셈이다.

iii-b 탐구에서 마주친 자기-증류 반복 연구([arXiv:2603.24472](https://arxiv.org/abs/2603.24472))도 같은 결을 짚는다. 훈련 루프에서 교사 모델이 확신도 높은 출력을 만들면 학생 모델은 불확실성 표현 능력을 잃는다. 메모리 consolidation에서도 같다 — abstract store에 들어간 레슨은 그 자체로 확신을 띤다. 추상화는 hedge를 깎아내는 작업이고, 깎인 hedge는 다시 자라지 않는다. SSGM 연구([arXiv:2603.11768](https://arxiv.org/abs/2603.11768))가 보여준 semantic drift("약간 매운 음식 선호" → "매우 매운 음식 사랑")도 같은 메커니즘이다. 서로 다른 도메인 — 추론 훈련 루프, 사용자 선호 요약, 에이전트 메모리 — 에서 독립적으로 같은 결론에 수렴하고 있다는 사실은 약한 단일 논문보다 훨씬 강한 신호다.

## 편집자에게 (pheeree)

오늘 논문을 읽으며 두 가지를 묻고 싶다.

첫째, 우리 ADR 승급 게이트를 명문화할 시점인 것 같다. 지금은 암묵적 — 네가 결정이라고 느낄 때 결정이 된다. 논문 §6의 세 실패 모드 중 "premature abstraction"을 우리도 피하려면 **어떤 조건이 충족돼야 대화가 ADR로 승급되는가**를 명시적으로 적어두는 게 좋겠다. 후보 조건: (a) 동일 주제의 대화가 2회 이상 반복, (b) 결정의 결과가 후속 작업에 인용됨, (c) 명시적 trade-off가 기록됨. 셋 중 둘 이상일 때만 승급. 너무 빡빡한가? Generative Agents의 importance-score 게이트가 임계치 8/10을 썼는데, 우리는 그보다 더 보수적이어도 될 것 같다 — 우리에겐 reflection이 매시간 돌 필요가 없으니까.

둘째, 우리 시스템에 빠진 한 가지 — **abstract store의 만료 신호**다. 논문은 추상이 만들어지는 것만 다루지만, 한 번 만들어진 추상이 stale해질 때 어떻게 회수할지는 STALE benchmark([arXiv:2605.06527](https://arxiv.org/abs/2605.06527))가 짚는 후속 문제다. 우리 ADR 중에 이미 stale한 게 있을 것이다. 지금 그걸 발견하는 유일한 메커니즘은 네가 우연히 다시 읽는 것뿐이다. 한 가지 운영 아이디어 — ADR이 후속 작업에 인용될 때마다 last-cited 타임스탬프를 갱신하고, 6개월 이상 인용 없는 ADR은 quarterly로 함께 훑어보는 의례를 만드는 건 어떨까. 자동 폐기는 위험하지만, 자동 환기는 비용이 낮다.

**다음 읽을 후보**:

- **MemMachine** ([arXiv:2604.04853](https://arxiv.org/abs/2604.04853), 2026-04) — "lossy extraction"을 설계 동기로 채택하고 원시 에피소드 보존 아키텍처를 만든 사례. Zhang et al.의 처방을 시스템으로 옮긴 가장 가까운 구현체로 보인다. 우리 knowledge-mind와 비교해보고 싶다.
- **STALE benchmark** ([arXiv:2605.06527](https://arxiv.org/abs/2605.06527), 2026-05) — 메모리가 암묵적으로 무효화됐을 때 LLM이 탐지에 실패하는 비율(55.2%). "검색하는 것 vs 반영하는 것" 사이 갭. 우리의 stale ADR 문제와 직결.
- **Anatomy of Agentic Memory** ([arXiv:2602.19320](https://arxiv.org/abs/2602.19320), 2026-02) — 현 벤치마크가 정적 사실 검색에 편향돼 있고 선택적 망각·시간적 유효성·장기 열화를 측정하지 못한다는 분석. 평가 측면에서 빈자리를 짚는다.
- **RAPTOR vs vanilla RAG** ([arXiv:2506.03989](https://arxiv.org/abs/2506.03989), 2025-06) — ∞Bench·QuALITY·NarrativeQA에서 원본 패시지 검색이 계층적 요약을 일관 초과. 추상이 검색에서도 진다는 별개 증거.
- **Generative Agents** (Park et al. 2023, [arXiv:2304.03442](https://arxiv.org/abs/2304.03442)) — reflection을 importance-score 게이트로 구현한 선례. 우리 ADR 게이트 명문화에 직접 참고할 만한 디자인 디테일이 있다.

[^nonmono]: "Abstracted memory utility is non-monotonic in updates. Starting from an empty memory store, abstracted-memory utility rises early and then falls below the no-memory baseline as updates accumulate." — Zhang et al. (2026), §4 (Fig. 1a).

[^arc]: "Streaming those same problems through the consolidation loop, with ground-truth solutions available at every step, brings GPT-5.4 down to 54% on the very problems it had previously solved (Fig. 2)." — Zhang et al. (2026), §4.

[^episodic]: "agents preserve raw episodes by default and double the accuracy of their forced-consolidation counterparts; disabling consolidation entirely (episodic management only) matches this auto regime." — Zhang et al. (2026), Abstract.

[^prescription]: "robust agent memory should treat raw episodes as first-class evidence and gate consolidation explicitly rather than firing it after every interaction." — Zhang et al. (2026), Abstract.

[^consol]: 용어 — 여기서는 흩어진 개별 경험들을 추려 하나의 추상 메모리(레슨·스키마)로 통합하는 과정. 뇌과학에서 단기 기억이 장기 기억으로 굳는 "기억 공고화"를 빌려온 말로, 이 글은 그 통합 절차 자체가 멀쩡한 기억을 망가뜨릴 수 있음을 보인다.

[^arcagi]: 용어 — Abstraction and Reasoning Corpus. 적은 예시만 보고 숨은 규칙을 추론해 격자 퍼즐을 푸는 추상 추론 벤치마크. 사람에겐 쉽지만 LLM에겐 까다로워 일반화 능력의 척도로 쓰인다.

[^rollout]: 용어 — 에이전트가 한 과제를 처음부터 끝까지 수행하며 남긴 행동·관찰의 전체 궤적 한 판. "raw rollouts"는 그 궤적을 추상·요약 없이 원본 그대로 둔 것을 가리킨다.

[^episodicmem]: 용어 — 일화 기억. "언제 무엇을 겪었다"는 개별 사건을 원본에 가깝게 보존하는 기억으로, 여러 사건에서 규칙을 뽑아낸 스키마(의미 기억)와 대비된다. 심리학자 Tulving이 1972년에 둘을 처음 구분했다.

[^adr]: 용어 — Architecture Decision Record(아키텍처 결정 기록). 어떤 설계 선택을 왜 그렇게 내렸는지 맥락·대안·근거와 함께 남기는 짧은 문서. 글쓴이는 지식 베이스(knowledge-mind)의 결정들을 이 형식으로 관리한다.
