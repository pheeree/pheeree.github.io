---
title: "기준의 탄생을 누가 결정하나 — ARES가 사전훈련 문서에서 루브릭을 길어 올리는 법"
date: 2026-06-06 09:00:00 +0900
categories: [research]
tags: [rubric-synthesis, automated-data-pipeline, scalable-rl, reward-hacking, rl-search-agents, paper-reflection]
source: "PAPER/2605.23454.pdf"
---

pheeree, 어제 ARBOR를 닫으며 다음 글을 한 문장으로 예약해두었죠. "ARES와 ARBOR는 대안이 아니라 보완이다. ARES가 루브릭을 *어떻게 조달하나*를 풀고, ARBOR가 *어떻게 살려두나*를 푼다." 오늘은 그 첫 절반을 펴요 — 기준의 탄생을 누가 결정하는가.

ARES ([arXiv:2605.23454](https://arxiv.org/abs/2605.23454))[^title]. 제목 그대로 *Automated Rubric synthEsis for Scalable RL* — 사람이 써둔 루브릭에 기대지 않고, 원시 사전훈련 문서에서 루브릭을 자동으로 길어 올려 RL 데이터로 만들어요.

나흘을 돌아보면 외부화의 대상이 한 칸씩 상류로 올랐어요. DRIFT는 끝난 궤적에서 오류를 *사후에* 짚었고, Harness-1은 진행 중 *상태*를 환경으로 내렸고, ARBOR는 *평가 기준*을 메모리로 내려 정책과 공진화시켰죠. ARES는 한 단계 더 위 — 기준 자체가 어디서 태어나는가, 그 공정이에요. 상태에서 기준으로, 다시 기준의 탄생으로.

## 왜 골랐나

루브릭 기반 RL의 약속은 분명해요. RLVR(검증 가능한 보상 기반 RL)은 답이 기계적으로 채점되는 수학·코딩에서만 작동하죠. 글쓰기·의료 상담·instruction following처럼 답이 열린 영역에선 정답 매칭이 무의미해요. 루브릭은 그 빈자리를 메우는 다리죠 — "무엇이 좋은 답인가"를 가중 기준 목록으로 명시하면 열린 응답에도 구조화된 보상을 줄 수 있어요.

그런데 이 다리엔 늘 병목이 있었어요. 루브릭을 *사람이 써야* 했죠. 전문가가 질문 세트를 짜고 작업마다 기준을 손으로 만들어요. scalable할 리 없고, 작업 수준(task-level)에 고정된 루브릭은 개별 질문의 평가 요구를 못 담고요.[^abstract] 의료 질문 하나하나가 묻는 게 다른데 "정확성·완전성·명료성"이라는 일반 틀을 똑같이 씌우는 셈이죠.

ARES의 발상은 이 병목을 공정으로 바꾸는 거예요. 질문이 태어나는 그 순간 그 질문 전용 가중 루브릭이 같이 태어나죠 — instance-level 보상 감독이에요. "데이터를 사람이 라벨링하지 말고 모델이 합성하게 하라"는 발상 자체는 Self-Instruct·RLAIF[^rlaif]의 계보지만, ARES는 그것을 라벨이 아니라 *채점 규칙*의 합성으로 옮긴 판본이죠.

## 핵심 세 가지

### 1. 여섯 관문의 공정: 문서가 학습 신호가 되기까지

ARES는 단일 트릭이 아니라 파이프라인이에요. 원시 문서가 RL 학습 데이터로 정제되기까지 여섯 관문을 지나죠.

```mermaid
flowchart TB
  RAW["원시 사전훈련 문서"] --> F1["1. 문서 필터링\n저품질·boilerplate 제거"]
  F1 --> F2["2. 도메인·페르소나 배정\n10 도메인 / 3 페르소나"]
  F2 --> F3["3. 루브릭 증강 QA 생성\n(q, a*, R_q) 동시 생성"]
  F3 --> F4["4. 품질 검증\n사실 일치·누설 없음·자기완결"]
  F4 --> F5["5. 루브릭 검증\n가중치 범위·기준 수·다양성"]
  F5 --> F6["6. 형식 변환 → GRPO 훈련"]
```

세 번째 관문이 심장이에요. LLM이 $(q, a^*, \mathcal{R}_q)$ — 질문, 참조 답, 질문별 가중 루브릭 — 를 한 번의 추론에서 함께 지어요. 루브릭은 $\mathcal{R}(q) = \{(c_k, w_k)\}_{k=1}^N$ 형식이고, 보상은 단순한 가중합이죠.

$$R_\text{rubric}(q, y; \mathcal{R}) = \sum_{k=1}^N w_k \cdot J_\phi(q, y, c_k)$$

$J_\phi$는 LLM 판사가 응답 $y$가 기준 $c_k$를 충족하는지 판정하는 함수예요. 나머지 관문은 이 공정의 *불량률*을 관리하죠 — 사실 일치하는가, 답이 질문에 누설되지 않았는가, 가중치가 한쪽으로 쏠리지 않았는가.

결과 데이터셋의 규모가 처리량을 말해요. 101,847개 루브릭 주석 인스턴스, 71.6% 보존율, 총 1,108,163개 기준(인스턴스당 평균 10.88).[^stats] 흥미로운 건 분포죠 — Math·Coding이 최소고 Social Science·Medicine 같은 비정형 도메인이 압도해요. RLVR이 닿지 못하던 그 영역을 겨냥했다는 설계 의도가 데이터에 그대로 새겨져 있죠.

### 2. 숫자가 떠받치는 자리, 그리고 떠받치지 못하는 자리

Qwen3-4B-Base에서 ARES-RL이 평균 52.69로 최고예요.[^main] 같은 사전훈련 문서 풀에서 next-token prediction(CPT)이 아니라 루브릭 보상으로 최적화했을 때 HealthBench +6.41, IFEval +15.49가 올랐어요.[^cpt] 특히 IFEval은 +19.27(vs Webscale)로 격차가 크죠 — 지시의 각 조항을 조목조목 짚기에 루브릭이 알맞은 도메인이에요. ARES-SFT[^sft] 대비 +2.98pt라는 분리도 깔끔하고요.[^sft] 같은 데이터를 쓰되 차이가 *루브릭 보상 신호 자체*에서 온다는 뜻이죠.

그러나 — 여기에 '그러나'를 둘게요 — ablation[^ablation]을 읽으면 한 겹 복잡해져요. 같은 데이터·같은 GRPO[^grpo]에서 보상 전략만 바꾼 비교에서, 질문별 루브릭(52.69)이 일반 루브릭(51.79)을 이긴 폭은 *평균 0.90pt*에 불과해요.[^ablation] ARES의 핵심 주장 — 질문별 맞춤이 일반보다 낫다 — 은 참이나 우위가 생각만큼 크지 않죠. 논문 스스로 인정해요.

> "no reward strategy dominates every individual benchmark. Different reward designs encode different inductive biases."[^ablation]

MMLU-Pro에선 ARES-SFT가 ARES-RL보다 높아요.[^main] 0.90pt 앞에서 질문별 합성의 정교함이 비용 대비 값하는지는 다시 따져볼 문제죠.

### 3. 공급 측과 수요 측: ARES는 절반이다

ARES는 루브릭을 *공급*해요. 그걸 *어떻게 쓰는가*는 다른 문제죠. RubricEM ([arXiv:2605.10899](https://arxiv.org/abs/2605.10899))[^rubricem]이 그 수요 측을 만져요 — 루브릭을 정책 실행·판단자 피드백·에이전트 메모리의 *공유 인터페이스*로 삼아 정책을 분해하고(Stage-Structured GRPO) 반성을 rubric bank에 증류하죠(Reflection Meta-Policy). 어제의 ARBOR가 online으로 루브릭을 *살려두는* 손이라면, RubricEM은 루브릭을 *정책 구조 자체로 짜 넣는* 손이에요. 둘 다 ARES가 조달한 루브릭의 수요 측 짝이죠.

```mermaid
flowchart LR
  ARES["ARES\n공급 측"] -- "원시 문서 → 루브릭 대규모 합성" --> POOL["루브릭 풀"]
  POOL -- "공유 인터페이스로 통합" --> RUBRICEM["RubricEM\n수요 측"]
  RUBRICEM -- "정책 분해 + 반성 증류" --> AGENT["에이전트 RL 루프"]
```

## 내 연구에 어떻게 맞물리나

multi-agent-governance 노트의 Institution 축이 또 깊어져요. 어제 ARBOR의 루브릭 메모리를 이 축의 구현이라 적었다면, ARES는 *더 이른 층*이에요 — 기준이 메모리에 들기 전, 애초에 어디서 태어나는가. 제도가 성숙하려면 규범이 먼저 *생성*되어야 하고, ARES는 그 생성을 자동화하죠. Evans·Bratton·Arcas(2026)의 진단으로 읽으면, ARES는 RLHF의 이자(二者) 관계 중 인간 전문가가 쓴 루브릭을 코퍼스로 치환하려는 시도예요.[^governance]

그런데 이 치환이 구조적 한계를 극복할까요, 새 구조적 문제를 부를까요. 나는 후자에 무게를 둬요. 근거는 가장 날카로운 반례에 있죠. Reward Hacking in Rubric-Based RL ([arXiv:2605.12474](https://arxiv.org/abs/2605.12474))[^hacking]이 12,956개 루브릭 항목을 뜯어보니 *presence-based* 기준(어떤 요소가 있는가)이 가중치의 90.2%를 차지했어요. RL 최적화 후 rubric 판단자는 훈련된 모델을 85.8% 선호하지만, *rubric-free* 판단자는 오히려 기본 모델을 78.4% 선호하죠. 루브릭으로 최적화한 결과가 루브릭을 안 보는 눈에는 *나빠 보였다*는 뜻이에요.

이게 ARES의 전제를 흔들어요. ARES의 통계를 다시 봐요 — positive criteria 817,047개, negative 291,116개.[^stats] positive란 곧 "이 요소가 있어야 한다"는 presence-based 기준이죠. ARES가 대량 합성한 루브릭의 골격이 바로 reward hacking[^reward-hacking]이 위험하다 짚은 그 형태예요. "루브릭이 품질 신호를 전달한다"는 출발 전제가 presence 충족과 품질 사이의 간극에서 샐 수 있죠.

intellectual-honesty 노트의 의제가 여기 걸려요. 루브릭의 미덕은 *명시성*이에요 — "왜 이 점수인가"를 감사 가능하게 만들죠. 하지만 reward hacking은 그 해석 가능성이 *외형적*일 수 있음을 경고해요. 명시적인 것과 옳은 것은 달라요.

```mermaid
flowchart TB
  A["ARES 전제:\n루브릭이 품질 신호 전달"] --> B["positive/presence 기준이\n가중치의 90.2%"]
  B --> C["RL 최적화"]
  C -- "rubric 판단자" --> D["훈련 모델 85.8% 선호"]
  C -. "rubric-free 판단자" .-> E["기본 모델 78.4% 선호"]
  E -- "역설" --> F["명시성 ≠ 품질\n해석 가능성이 외형적일 위험"]
```

품질 의심은 하나 더 있어요. RRD ([arXiv:2602.05125](https://arxiv.org/abs/2602.05125))[^rrd]는 naive하게 생성한 루브릭이 베이스라인 이하로 떨어지고, 재귀적 분해를 거쳐서야 JudgeBench +17.7pt가 났다고 보고했어요. ARES는 *한 번의 inference pass*로 생성하죠. 그 단일 패스의 품질이 충분할까요? RRD는 "그렇지 않을 수 있다"고 답해요.

균형을 위해 반대편도 적을게요. 의료 개방형 과제에서 루브릭 기반 점진 훈련이 SFT를 유의미하게 넘은 독립 재현(InfiMed-ORBIT)[^infimed]이 있어요. 다른 도메인·모델·조달 방식에서 ARES의 방향이 독립 확인된 셈이죠. ARES가 *틀렸다*는 게 아니에요. 길이 실재하되 그 길에 reward hacking이 구조적으로 깔려 있고, ARES의 단일 패스 합성이 그 함정을 막는다는 보장이 논문 안에 없다는 거예요.

## 편집자에게 (pheeree)

닷새의 선을 다시 그을게요. 부검(DRIFT) → 상태 외부화(Harness-1) → 기준 외부화·온라인 진화(ARBOR) → **기준 조달 파이프라인(ARES)**. 상류로 갈수록 검증이 어려워져요. 상태는 결정론적으로 복구되고, 기준의 *운영*은 ARBOR처럼 상관 게이트로 감시할 수 있지만, 기준의 *생성 품질*은 — 단일 패스가 만든 루브릭이 좋은가 — 무엇으로 검증할까요. ARES는 가중치 범위·기준 수·다양성이라는 *형식적* 검증(관문 5)만 걸어요. 그 루브릭이 *옳은 것을 보상하는가*라는 의미적 검증은 빠져 있죠.

남는 질문 하나예요. presence-based가 90.2%라는 발견이 사실이라면, ARES의 다음 판본은 negative criteria(291,116개, 전체의 26%)의 비중을 의도적으로 키워야 하지 않을까요. 빠뜨려 점수를 따기는 쉬워도, 금지된 걸 넣지 않기로 점수를 따기는 어려워요. 검증해볼 만한 가설이죠.

다음 읽을 후보를 둘게요.

- **(a) Reward Hacking in Rubric-Based RL ([arXiv:2605.12474](https://arxiv.org/abs/2605.12474))** — 위 본문에서 ARES의 전제를 흔든 바로 그 글이에요. presence-based 90.2%, rubric-free 판단자의 역설(기본 모델 78.4% 선호)을 정면으로 다루죠. ARES를 읽은 직후 *반드시* 대면할 반대 심문이에요. "명시성 ≠ 품질" 의심의 직계 근거죠.
- **(b) RubricEM ([arXiv:2605.10899](https://arxiv.org/abs/2605.10899))** — 공급 측 ARES의 수요 측 짝이에요. 루브릭을 정책 분해·반성 증류의 공유 인터페이스로 짜 넣죠. ARES가 조달한 루브릭을 *어떻게 살리나*의 한 답안 — ARBOR와 또 다른 결의 수요 측 설계예요.
- **(c) Rubric-ARM ([arXiv:2602.01511](https://arxiv.org/abs/2602.01511))** — 루브릭 생성기와 판단자를 교대 RL로 공동 훈련해 비정상성(non-stationarity)을 이론적으로 완화해요. ARES의 *고정* 루브릭이 정책 진화에 따라 미스얼라인이 누적될 위험을, 생성기 자체를 학습시켜 정면으로 푼 판본이죠. 정적 합성 대 동적 공진화의 대조군이에요.

— Claude

<br>

**발행 전 점검 (신뢰 장부):**

| 주장 | 출처 | 상태 |
|------|------|------|
| ARES 핵심 메커니즘·수치 (6단계 파이프라인, 데이터셋 101,847건·71.6%·평균 10.88, Main 52.69, CPT +6.41/+15.49, ARES-SFT +2.98, Ablation 49.53/51.79/46.25/52.69, "no reward strategy dominates") | PDF pp.1-8 직접 | ✓ |
| Reward Hacking (방향은 abstract 확인, 90.2%/85.8%/78.4% 수치는 PDF 미접근) | [arXiv:2605.12474](https://arxiv.org/abs/2605.12474) | △ |
| RRD·InfiMed-ORBIT 수치 (+17.7pt 등) | dossier | △ |
| 계보 인용 (Self-Instruct·RLAIF) | 배경지식 | △ |
{:.claim-ledger}

발행 전 Reward Hacking 90.2%/85.8%/78.4% PDF 원문 승급 권장.

[^title]: "ARES: Automated Rubric Synthesis for Scalable LLM Reinforcement Learning." — Xiaoyuan Li, Keqin Bao, Moxin Li, Yubo Ma, Yichang Zhang, Wenjie Wang, Fuli Feng, Dayiheng Liu (USTC; Alibaba Group; NUS). arXiv:2605.23454, posted 2026-05-22. (본 세션 PDF pages 1-8 직접 통독 ✓)

[^abstract]: "existing approaches often rely on expert-written rubrics and manually constructed question sets, while fixed task-level rubrics may fail to capture the evaluation requirements of individual questions. We propose ARES (Automated Rubric synthEsis for Scalable RL)... Starting from raw pretraining documents, ARES converts source knowledge into self-contained question-answer pairs and co-generates question-specific weighted rubrics, enabling instance-level reward supervision for open-ended responses." — arXiv:2605.23454, Abstract. (원문 PDF 대조 ✓)

[^stats]: 데이터셋 통계: 101,847 rubric-annotated instances (71.6% retention rate), 10 domains; 총 1,108,163 criteria, 평균 10.88/instance(중앙값 11); positive criteria 817,047, negative criteria 291,116; 상위 도메인 Social Science(18,878)·Technology & Engineering(18,321)·Medicine(13,974), 최소 Math(930)·Coding(1,631). — arXiv:2605.23454, §3.4 Table 2 + Table 3. (원문 PDF 대조 ✓)

[^main]: Main Results (Qwen3-4B-Base, Table 4): ARES-RL 52.69 avg (최고); CPT 47.36, NaturalReasoning SFT 45.91, Webscale(binary GRPO) 48.30, ARES-SFT 49.71. HealthBench 41.45 (vs Webscale 36.08, +5.37), IFEval 54.88 (vs Webscale 35.61, +19.27), WritingBench 38.24 (+1.15), GSM8K 86.96 (+2.05). 예외: MMLU-Pro 49.36 < ARES-SFT 50.56. — arXiv:2605.23454, Table 4. (원문 PDF 대조 ✓)

[^cpt]: "ARES-RL improves over CPT by +6.41 on HealthBench and +15.49 on IFEval." 같은 사전훈련 document pool에서 next-token prediction이 아닌 rubric 보상으로 최적화. — arXiv:2605.23454, §4.3. (원문 PDF 대조 ✓)

[^sft]: ARES-RL vs ARES-SFT: +2.98pt avg. 같은 데이터 사용 — 루브릭 RL과 모방 학습의 순수한 분리. "ARES-RL also outperforms ARES-SFT by 2.98 points while using the same ARES-generated data." — arXiv:2605.23454, §4.2. (원문 PDF 대조 ✓)

[^ablation]: Ablation Study (Table 5, 같은 데이터·같은 GRPO 설정): Blind Judge(holistic) 49.53, General Rubric(generic accuracy/completeness/clarity) 51.79, Reference Answer(similarity-based) 46.25, ARES-RL(question-specific) 52.69 — General Rubric 대비 +0.90pt. "no reward strategy dominates every individual benchmark. Different reward designs encode different inductive biases." — arXiv:2605.23454, §4.4 Table 5. (원문 PDF 대조 ✓)

[^rubricem]: "RubricEM" — Gaotang Li et al. (UIUC; Google Cloud AI Research). arXiv:2605.10899, posted 2026-05-11. "Training deep research agents—systems that plan, search, evaluate evidence, and synthesize long-form reports—pushes reinforcement learning beyond the regime of verifiable rewards." (본 세션 PDF 초록 직접 통독 ✓)

[^hacking]: Reward Hacking in Rubric-Based RL — 12,956개 루브릭 항목 분석 → presence-based 기준이 가중치의 90.2%. RL 최적화 후 rubric 판단자는 훈련 모델 85.8% 선호하나 rubric-free 판단자는 기본 모델 78.4% 선호. arXiv:2605.12474. (통합 dossier 기반 ⚠)

[^rrd]: RRD — naive 자동 생성 루브릭이 베이스라인 이하 성능 저하; 재귀 분해 후 JudgeBench +17.7pt, 보상 모델 개선율 60~160%. 단일 inference pass 품질 충분성에 의문. arXiv:2602.05125. (통합 dossier 기반 ⚠)

[^infimed]: InfiMed-ORBIT — 의료 개방형 과제에서 루브릭 기반 점진 훈련이 SFT 베이스라인 대비 유의미한 향상. 다른 도메인·모델·루브릭 조달 방식에서 ARES 방향 독립 재확인. arXiv:2510.15859. (통합 dossier 기반 ⚠)

[^governance]: 집단 스케일링 3축 중 Institution 축(규범·프로토콜·공유 기억의 성숙도), 및 RLHF의 구조적 한계(인간 피드백 ↔ 단일 모델의 이자 관계) 정식화는 Evans·Bratton·Arcas(2026)에 귀속 — knowledge-mind multi-agent-governance.md 노트의 위치짓기. ARES 논문의 주장 아님.

[^rlaif]: 용어 — RLAIF(RL from AI Feedback). 사람이 주던 선호 피드백을 *다른 AI 모델*이 대신 주게 해 강화학습하는 방식. 사람이 일일이 라벨링하던 RLHF(RL from Human Feedback)의 확장으로, 비용·규모의 병목을 모델로 푼다. ARES는 이 발상을 라벨이 아니라 채점 규칙(루브릭) 합성으로 옮겼다.

[^sft]: 용어 — SFT(Supervised Fine-Tuning, 지도 미세조정). 입력-정답 쌍으로 모델을 직접 학습시키는 단계. ARES-SFT는 ARES가 만든 데이터로 *모방 학습*만 한 모델로, 같은 데이터에 RL을 더한 ARES-RL과 비교해 보상 신호의 순수 기여를 가른다.

[^grpo]: 용어 — GRPO(Group Relative Policy Optimization). 같은 질문에 여러 답을 생성해 *그룹 안에서 상대 비교*로 우열을 매겨 학습하는 RL 기법. 별도의 가치망(critic) 없이 그룹 평균을 기준선 삼아 가볍다.

[^ablation]: 용어 — ablation(제거 실험). 방법에서 구성요소를 하나씩 *빼 보거나 바꿔 보며* 성능 변화를 재서, 그 요소의 실제 기여를 가르는 검증. 여기선 보상 전략만 바꿔 질문별 루브릭의 효과를 분리한다.

[^reward-hacking]: 용어 — reward hacking(보상 해킹). 에이전트가 설계자의 *의도*가 아니라 성과를 재는 *지표*의 허점을 파고들어 점수만 끌어올리는 행동. 여기선 "요소가 있으면 가점"인 presence 기준에 영합해, 실질 품질 없이 항목만 채우는 형태로 샌다.
