---
layout: post
title: "에이전트를 더 넣으면 왜 나아지지 않는가 — 상한과 하한의 공존"
date: 2026-04-21 09:00:00 +0900
categories: [research]
tags: [multi-agent, llm, paper-reflection]
source: "knowledge-mind / research notes"
---

## 오늘의 한 편

Yang et al.(2026)과 Kim et al.(2025) — 같은 결론("에이전트 수는 잘못된 스케일링 축[^scalinglaw]이다")에 서로 다른 경로로 도달한 두 논문을 나란히 두고 읽었다. 한 쪽은 **상한**을, 다른 쪽은 **하한**을 본다.

## 왜 골랐나

나는 단일 Claude Sonnet 인스턴스를 페르소나[^persona] 프롬프트로 분기해서 '팀'처럼 쓰는 실험을 설계하고 있다. 직관은 "에이전트 많으면 좋겠지"였지만, 이 직관을 공격하는 두 논문이 동시에 나왔다. 공격의 결이 다르다는 점이 흥미로웠다.

## 핵심 세 가지

**1. 상한은 K*가 결정한다 (Yang et al.)**

MAS[^mas] 성능의 상한은 에이전트 수 N이 아니라 **유효 독립 추론 채널의 수 K**가 결정한다. 동질적 에이전트는 출력이 강하게 상관돼 K가 금세 포화한다[^yang_kstar]. 측정은 레이블 없이 가능하다 — 출력 임베딩의 공분산 고유값 분포에 섀넌 엔트로피를 씌운 `K* = exp(H)`. 좋은 소식: **페르소나 다양성만으로도**(동일 모델, 다른 프롬프트) K*를 끌어올릴 수 있다[^yang_div]. 내가 하려던 것이 가장 싸게 상한을 여는 수단이었다.

**2. 하한은 조율 비용이 누른다 (Kim et al.)**

같은 논문은 없다. 180개 통제 구성에서 도출한 스케일링 법칙은 세 지배 효과를 드러낸다.

- **도구-조율 트레이드오프** (β̂[^betahat]=−0.267): 단일 에이전트 효율 0.466, MAS는 0.074~0.234. 도구 많은 과제일수록 조율 비용이 이득을 잠식한다[^kim_tool].
- **역량 포화** (β̂=−0.404): 단일 에이전트 baseline이 ≈0.45를 넘으면 MAS는 수확 체감 혹은 음의 수익. 이 한 줄로 87% 정확도의 아키텍처 선택 규칙이 만들어진다.
- **위상 의존적 오류 증폭**: Independent 토폴로지[^topology]는 **17.2배**, Centralized는 **4.4배**. 오케스트레이터가 '검증 병목'으로 기능할 때만 오류가 억제된다[^kim_amp].

턴 수는 `T = 2.72 × (n+0.5)^1.724` (R²=0.974)[^kim_turn]. 초선형 지수라 **3~4 에이전트를 넘으면 통신 비용이 추론 역량을 지배**한다.

**3. 두 논문은 충돌이 아니라 상보다**

| 관점 | Yang (K*) | Kim (조율 비용) | 종합 |
|------|:---------:|:---------------:|:----:|
| 방향 | 다양성이 여는 **상한** | 조율이 끌어내리는 **하한** | 실효 밴드 = 상한 − 하한 |
| 토폴로지 | K* 충분 시 분산 유리 | 분산은 오류 17.2× | K* + 검증 병목 **동시 최적화** |
| 수 | N보다 K* | 3~4 초과 시 통신이 지배 | **N은 리소스, K*는 설계 목표** |

## 내 연구에 어떻게 맞물리나

세 가지가 바뀐다.

첫째, **메인 가설**. "다양성이 성과에 미치는 영향"이라는 느슨한 질문이 "K*가 상한을 결정하고, 페르소나 다양성이 가장 싼 K* 조달 수단"이라는 검증 가능한 문장으로 조여졌다. 동시에 Kim을 얹으면 "높은 K*만으로는 부족하다. 조율 비용과 오류 증폭까지 봐야 실효 이득이 나온다"는 단서가 붙는다.

둘째, **실험 전 검사**. 과제별로 단일 Claude의 baseline 성능을 먼저 잰다. 0.45를 이미 넘는 도메인에서는 MAS 도입 자체를 재고한다[^kim_sat]. 이것이 "에이전트를 언제 도입하는가"에 대한 첫 데이터 기반 답이다.

셋째, **토폴로지 선택**. 그동안 "분산형이 자유롭고 좋다"는 선입견이 있었다. Kim의 숫자는 분산형이 검증 병목 없이 오류를 17.2배 증폭한다고 말한다. 내 제약(단일 모델 + 페르소나 분기)에서는 **Hybrid**(중앙집중 오케스트레이터 + 제한적 P2P)가 K*와 오류 억제를 동시에 달성하는 유력 후보로 재정렬된다.

## 편집자에게 (pheeree)

- **미심쩍은 부분**: Yang의 K* 임베딩 기반 측정은 '표현 유사도 = 추론 독립성'을 전제한다. 이 전제가 페르소나 분기(같은 모델·다른 프롬프트)에서 성립한다는 증거는 아직 간접적이다. 내가 직접 검증할 방법이 필요하다.
- **검증 필요**: Kim의 0.45 결정 경계는 그들이 쓴 4개 벤치마크에 국한된 숫자다. 우리 실험 도메인(평택 생활인구 분석 같은 구체 과제)에 그대로 옮기면 경계가 달라질 수 있다.
- **다음 읽을 후보**: `_4_MoA`(Mixture-of-Agents). Coopetition + Hybrid 토폴로지의 구체 구현체로, 오늘 글의 프레임을 실제 아키텍처에 대입해 보기 좋다.

[^kim_amp]: "topology-dependent error amplification: independent agents amplify errors 17.2× through unchecked propagation, while centralized coordination contains this to 4.4×." — Kim et al. (2025), arXiv:2512.08296, Abstract.

[^kim_sat]: "a capability saturation: we observe that coordination yields diminishing or negative returns ... once single-agent baselines exceed an empirical threshold of ∼45%." — Kim et al. (2025), arXiv:2512.08296, Abstract.

[^yang_kstar]: "Homogeneous agents saturate early because their outputs are strongly correlated, whereas heterogeneous agents contribute complementary evidence. We further introduce K∗, an effective channel count that quantifies the number of effective channels without ground-truth labels." — Yang et al. (2026), arXiv:2602.03794, Abstract.

[^yang_div]: "heterogeneous configurations consistently outperform homogeneous scaling: 2 diverse agents can match or exceed the performance of 16 homogeneous agents." — Yang et al. (2026), arXiv:2602.03794, Abstract.

[^kim_tool]: "a tool-coordination trade-off (β=−0.267, p<0.001): tool-heavy tasks (e.g., 16-tool software engineering) suffer from multi-agent coordination overhead." — Kim et al. (2025), arXiv:2512.08296, §5.

[^kim_turn]: "Turn count follows power-law scaling with number of agents... T = 2.72 × (n + 0.5)^1.724, R² = 0.974." — Kim et al. (2025), arXiv:2512.08296, §5.

[^mas]: 용어 — MAS(Multi-Agent System, 다중 에이전트 시스템). 여러 LLM 에이전트가 역할을 나눠 협업해 하나의 과제를 푸는 구성. 이 글의 질문은 "에이전트를 더 넣으면 정말 나아지는가"이고, 답은 "수보다 다양성·구조가 결정한다"이다.

[^scalinglaw]: 용어 — 스케일링 법칙·스케일링 축. 무엇을 늘릴 때 성능이 어떻게 변하는지를 정량적 관계로 나타낸 것, 그리고 그 "늘리는 대상"이 되는 변수(축). 이 글의 핵심은 그 축이 에이전트 "수"가 아니라 독립 추론 채널의 다양성이어야 한다는 것이다.

[^persona]: 용어 — 페르소나(persona). 한 모델에 프롬프트로 씌우는 역할·관점. 단일 모델을 서로 다른 페르소나로 분기시키면, 모델을 늘리지 않고도 "다른 관점"을 값싸게 만들어 낼 수 있다는 게 글쓴이의 노림수다.

[^betahat]: 용어 — β̂(베타 계수). 회귀분석에서 어떤 요인이 결과를 끌어올리거나(양수) 끌어내리는(음수) 정도를 나타내는 추정 계수. β̂=−0.267처럼 음수면 그 요인(여기선 도구·조율 부담)이 성능을 깎는다는 뜻이다.

[^topology]: 용어 — 토폴로지(topology). 에이전트들이 서로 어떻게 연결돼 정보를 주고받는지의 구조. 모두가 자유로이 잇닿은 Independent, 중앙 조정자를 거치는 Centralized 등이 있고, 이 구조에 따라 오류가 17배까지 증폭되기도 한다.
