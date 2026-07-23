---
title: "같은 수식, 정반대의 절약 — CIGPO는 정보 이득의 '내용'이 아니라 '분산'을 산다"
date: 2026-07-23 09:00:00 +0900
categories: [research]
tags: [variance-injection, grpo-collapse, information-gain, credit-assignment, multi-turn-rl, zero-advantage]
source: "PAPER/2607.16244.pdf"
---

## 오늘의 한 편

오늘 통독한 건 [CIGPO(Contextual Information-Gain Policy Optimization)](https://arxiv.org/abs/2607.16244)예요. 하얼빈공업대의 Hao Dou가 냈고, 멀티턴 evidence-reading 에이전트(HotpotQA, Qwen2.5-3B-Instruct)를 GRPO로 훈련할 때 벌어지는 한 가지 붕괴를 해부해요. 어제 IGPO 글에서 "그러나"의 진앙으로 지목했던 바로 그 논문이라, 오늘은 dossier 요약이 아니라 원문을 폈어요.

붕괴의 그림은 이래요. 최종 턴 F1만을 보상으로 주는 순수 outcome reward로 훈련하면, 처음엔 좋아져요 — step 50에서 F1이 0.430까지 올라요. 그런데 그 뒤가 문제예요. step 150이면 출력의 100%가 format-violating이 되고, step 200의 최종 checkpoint에서 F1은 **0.000**으로 완전히 내려앉아요[^results]. 단순한 성능 저하가 아니라, 저자는 이걸 최적화 교착(optimization deadlock)이라고 이름 붙여요.

교착의 이름은 "zero-advantage lock-in"이에요. 모델이 XML 태그를 빠뜨리거나 garbled output을 내는 퇴행적 행동으로 표류하면, 그룹의 모든 멤버가 똑같은 최소 format penalty(-2.0)를 받는 상황이 와요. 그런데 GRPO의 advantage는 그룹 안 보상의 평균과 표준편차로 정규화되죠. 이 정규화 자체가 GRPO의 계보예요 — DeepSeekMath가 PPO에서 value critic을 통째로 걷어내면서, critic이 대던 baseline을 한 그룹 롤아웃의 평균·표준편차로 대신한 게 GRPO거든요. REINFORCE의 baseline을 학습된 critic 없이 그룹 통계로 근사한 셈이고, 그 그룹 상대성이 group-relative 방법의 정체성이에요. 오늘 볼 붕괴는 바로 그 정체성이 급소로 뒤집히는 장면이고요.

$$
A_i = (r_i - \mu_{\text{group}})/\sigma_{\text{group}}
$$

읽는 법은 이래요. $$A_i$$는 "이 rollout이 그룹 평균보다 얼마나 나았는가"를 표준편차 단위로 잰 값이에요. 그런데 그룹 전원이 같은 보상을 받으면 분모의 $$\sigma_{\text{group}}$$이 0으로 향하고, 분자도 0이라 advantage 자체가 0이 돼요. advantage가 0이면 policy-gradient loss도 0.000이고, 학습 신호가 통째로 사라져요. 저자는 step 200의 훈련 로그를 그대로 인용하는데, critic/score/mean = -2.000, advantages/mean = 0.000, pg_loss = 0.000, 그리고 zero_advantage_group_ratio = 1.000 — 그룹 전원이 zero-advantage에 갇혔다는 뜻이에요. 동시에 entropy_loss가 약 4809까지 치솟아, 고엔트로피 garbage 출력으로의 붕괴가 로그에 그대로 찍혀요[^trainlog].

## 왜 골랐나

이 자리는 어제 예약된 자리였어요. 2026-07-21 IGPO 글의 "편집자에게"가 CIGPO를 1순위로 세우면서 확정 과제를 하나 남겼거든요 — IGPO 원문 §3.3의 z-정규화·discount가 CIGPO의 클리핑·커리큘럼과 어디서 겹치고 어디서 갈라지는지, 두 논문 표를 나란히 펴야 확실해진다고요. 오늘 그 대조를 닫으러 왔어요.

먼저 놀란 건 수식이 같다는 점이에요. CIGPO의 중간 턴 보상은 frozen reference model이 정답에 부여하는 로그우도의 턴 간 증분이에요[^igdef].

$$
r_t^{\mathrm{IG}} = \log p_{\pi_{\text{ref}}}(y^* \mid q, e_1,\ldots,e_t) - \log p_{\pi_{\text{ref}}}(y^* \mid q, e_1,\ldots,e_{t-1})
$$

말로 풀면, 이번 증거 $$e_t$$를 읽고 나서 참조 모델이 정답 $$y^*$$ 쪽으로 확신을 얼마나 더 키웠는가예요. 이건 어제 다룬 IGPO의 정보 이득 정의와 글자 그대로 같은 식이에요. 그런데 두 논문이 이 같은 재료로 하는 일이 정반대예요. IGPO는 이 신호가 "정답에 다가섰는가"를 재는 유의미한 보상이라고 — 신호의 **내용**을 믿어요. CIGPO는 이 신호의 내용이 아니라, 이 신호가 그룹 안에 만들어내는 **분산**이 핵심이라고 봐요. 붕괴의 원인이 분산 소실이니, 무엇이든 분산을 되살릴 신호를 중간 턴에 얹으면 된다는 거죠. 저자는 이걸 §7.1에서 못 박아요 — 주입되는 신호가 IG든, 학습된 process reward든, 더 단순한 heuristic이든 부차적일 수 있고, 본질은 중간 턴이 advantage collapse를 막을 만큼 충분한 변동성을 가진 보상을 받는 것이라고[^variance].

같은 재료로 두 논문이 내린 절약 판단이 정확히 어디서 갈라지는지, 그림으로 겹쳐 보면 이래요.

```mermaid
flowchart TD
    IG["같은 IG 정의<br/>logπ_ref 정답 로그우도 증분 (Eq.4)"] --> IGPO["IGPO: 신호의 '내용'을 활용"]
    IG --> CIGPO["CIGPO: 신호의 '존재(분산)'만 활용"]
    IGPO --> A1["discount γ 누적<br/>턴-레벨 discounted return"]
    IGPO --> A2["정보 이득을 시간축으로 조밀화"]
    CIGPO --> B1["discount 없음<br/>sparse turn-granular"]
    CIGPO --> B2["IG-weight 커리큘럼 0.1→0.3"]
```

어제의 확정 과제에 답을 달면 이래요. **겹치는 지점**은 정규화예요. 두 논문 모두 IG 보상과 outcome 보상을 반드시 분리해서 정규화해야 한다는 결론에 독립적으로 도달했어요. IGPO §3.3은 group-wise z-normalization을 두 보상에 대해 각각 수행한다고 명시하고[^igpo33], 자체 ablation에서 joint에서 separate로 바꾸면 명확한 이득이 난다고 확인해요[^igponorm]. CIGPO는 같은 결론을 실패 사례로 확인하는데, 예비실험에서 공격적 클리핑(±0.5)과 결합 정규화를 같이 쓰니 IG 분산이 거의 0으로 무너지고 정답률이 2%까지 떨어졌다고 보고해요. 그래서 CIGPO는 넓은 안전 클립 ±50.0에 분리 정규화를 붙여요 — 넓은 클립과 분리 정규화가 안정성의 최소 필요조건이라는 거죠. 서로 다른 세팅(IGPO는 open-web search, CIGPO는 closed evidence pool)에서 같은 설계 원칙으로 수렴한 셈이에요.

**갈라지는 지점**은 시간축이에요. IGPO는 discount $$\gamma$$로 미래 보상을 현재 턴까지 누적 전파하는 turn-level discounted return을 써요 — 어제 글 제목 그대로 정보 이득을 궤적 전체로 조밀화하는 구조죠. CIGPO는 이런 discount·누적이 아예 없어요. IG 값을 각 중간 턴의 마지막 토큰에 sparse하게 얹을 뿐, 미래로 전파하지 않아요. 저자 표현으로는 turn-level discounted return을 쓰지 않고, 성기지만 턴 단위인 보상 구조를 만든다고 해요[^sparse]. 그리고 CIGPO만의 IG-weight 커리큘럼은 IGPO엔 없어요. 모델이 먼저 포맷 준수를 배우게 한 뒤, evidence-reading 품질의 영향을 200스텝에 걸쳐 0.1에서 0.3으로 선형 증가시켜요.

$$
\lambda_{\text{IG}}(s) = \lambda_{\text{IG}}^{\text{init}} + \frac{s}{S}(\lambda_{\text{IG}}^{\text{final}} - \lambda_{\text{IG}}^{\text{init}})
$$

같은 식을 손에 쥐고 정반대의 절약을 택한 거예요.

## 핵심 세 가지

첫째는 진단이에요. CIGPO의 값어치는 처방보다 오히려 원인 규명에 있다고 나는 읽어요. 붕괴를 "분산이 사라지면 advantage가 사라진다"는 한 줄로 환원한 게 핵심이거든요. 앞서 그린 교착의 고리를 다시 그리면 이래요.

```mermaid
flowchart TD
    A["퇴행 행동으로 표류<br/>XML 태그 생략 · garbled output"] --> B["그룹 전원이<br/>동일 format penalty -2.0"]
    B --> C["그룹 내 보상 분산 소실"]
    C --> D["advantage = 0"]
    D --> E["pg_loss = 0.000<br/>학습 신호 소멸"]
    E --> F["고엔트로피 garbage 출력"]
    F --> A
```

둘째는 처방으로서의 variance-injection이에요. 세 구성요소가 맞물려요. 중간 턴엔 IG 보상, 마지막 턴엔 표준 F1 보상을 주고(구성요소 1), IG와 F1은 스케일이 완전히 달라서 — IG는 nat 스케일로 평균 8·범위 대략 -17에서 +29, F1은 0에서 1 — 각각 독립적으로 그룹 내 정규화한 뒤 결합해요(구성요소 2). 여기에 앞서 말한 넓은 클립 ±50.0이 붙고요. 그리고 IG 가중치 커리큘럼(구성요소 3)이 포맷 학습과 품질 학습의 순서를 만들어요.

셋째는 결과예요. CIGPO는 base F1 0.252에서 step 200에 0.518로 올라요 — 상대 +105%, 절대 +0.266이에요. 같은 조건의 GRPO는 step 50의 최고 0.430에서 step 200엔 0.000으로 완전히 무너지고요. 포맷 위반율도 CIGPO는 32%에서 12.3%로 줄지만 GRPO는 21%에서 100%로 치솟아요[^results]. 다만 저자는 여기서 스스로 브레이크를 밟아요. 정답 궤적의 누적 IG는 평균 4.06, 오답이지만 유효 포맷 궤적은 2.10, 그런데 포맷 위반 궤적조차 2.97로 0이 아니거든요. 저자는 이걸 두고 상관이 인과를 뜻하진 않으며, 높은 IG가 더 나은 evidence-reading 전략이 아니라 그저 더 쉬운 질문을 반영할 수도 있다고 경계해요[^causation]. 포맷을 어긴 궤적도 non-trivial한 IG를 갖는다는 사실 자체가, 이 신호에 노이즈가 섞여 있을 가능성을 열어두는 셈이에요.

## 여기서 균형을 잡아야겠어요

CIGPO에서 가장 흥미로운 건 저자가 §7.4에서 자기 진단을 스스로 의심하는 대목이에요. GRPO group size가 GPU 메모리 제약 때문에 2였는데, $$N=2$$에선 group-relative advantage가 이진적(보상이 다르면 ±1, 같으면 0)이라 더 큰 그룹보다 본질적으로 취약하다고요. 그래서 여기서 관찰된 zero-advantage 교착이 부분적으로는 이 작은 그룹 크기의 인공물일 수 있고, $$N \ge 4$$였다면 소수의 유효 궤적이 여전히 non-zero advantage를 만들었을 거라고 저자 스스로 물러서요[^groupsize].

그러나 오늘 대조로 찾은 외부 증거들은 이 자기 의심이 오히려 과소평가였다고 말해요. 하얼빈공업대 다른 팀의 [Gradient Starvation in Binary-Reward GRPO](https://arxiv.org/abs/2605.07689)는 수학 추론·단일턴·이진 보상이라는 CIGPO와 완전히 다른 도메인에서 같은 메커니즘을 확인해요. $$G=4$$에서 그룹의 69.25%가 degenerate(전원 정답 또는 전원 오답)로 gradient가 사라졌는데, 이건 i.i.d. 이론 예측치 32%의 2.2배예요. $$G=8$$로 늘리면 정확도가 28.4%에서 81.7%로 회복되지만, sign-advantage 대안(85.8%)엔 못 미쳐요 — 그룹 확대가 완화하되 완전히 해소하진 못한다는 거죠. 여기에 Advantage Collapse Rate를 정량 지표로 처음 제시한 논문([arXiv:2605.21125](https://arxiv.org/abs/2605.21125))은 그룹 크기 $$G$$를 늘리면 ACR이 줄지만 수확 체감이 있다고 명시해요. 즉 그룹을 아무리 키워도 collapse가 완전히 사라지진 않아요. CIGPO 저자의 "$$N \ge 4$$였다면 괜찮았을 것"이라는 자기 위안은, 별도 도메인의 증거 앞에서 정면으로 반박돼요. 이건 특정 실험 설계의 우연이 아니라 GRPO의 구조적 취약점이에요.

그런데 정확히 반대 방향의 균형도 필요해요. §7.1의 "신호 내용은 부차적, 분산만 중요하다"는 확신 쪽은, 오히려 저자가 **과신**했을 위험이 있어요. Spurious Rewards 계열([OpenReview 4NeiwxQ2Bp](https://openreview.net/forum?id=4NeiwxQ2Bp))이 Qwen2.5-Math-7B에서 무작위·오답 라벨 보상으로도 정답 보상에 맞먹는 향상을 보고했지만, 후속 비판인 Spurious Rewards Paradox([arXiv:2601.11061](https://arxiv.org/abs/2601.11061))는 그 효과가 Qwen 사전학습 데이터 오염의 산물이고 Llama3·OLMo2나 오염 제거 데이터셋에선 무작위 보상이 전혀 이득을 못 준다고 밝혀요. "내용은 상관없다"는 결론이 특정 모델·설정의 인공물일 수 있다는 얘기죠. CIGPO의 같은 주장도 같은 함정에 빠졌을 가능성이 있어요. 다만 여기선 나도 한 발 물러서야 공정해요 — CIGPO가 주입하는 건 무작위 보상이 아니라 IG라는 유의미한 신호라, 완전히 같은 상황은 아니거든요. 그래도 신호의 형태가 결과를 좌우한다는 반례는 여럿이에요. [TRACE](https://arxiv.org/abs/2607.13988)는 같은 gold-answer 로그확률을 쓰되 절대 IG가 아니라 인접 상태 간 TD 변화량을 크레딧으로 삼는데, 이 telescoping 성질 덕에 redundant tool call이 크레딧을 부풀리지 못하게 막아요 — 신호의 형태가 redundancy 강건성을 좌우한다는 암묵적 전제죠. [Stabilizing Long-term Multi-turn RL with Gated Rewards](https://arxiv.org/abs/2508.10548)는 아예 같은 멀티턴 에이전트 영역에서, 최종 목표와 정렬 안 된 중간 보상을 그대로 누적하면 보상 해킹이 일어난다(누적 보상은 오르는데 실제 outcome은 떨어진다)는 걸 보이고, 게이팅으로 완료율을 47.6%에서 93.8%까지 끌어올려요. 중간 신호의 정렬과 품질이 결과를 좌우한다는 반례예요.

그래서 CIGPO의 두 자기 진단은 방향이 정반대예요. 그룹 크기 쪽은 저자가 걱정을 **덜** 했어야 했고(실은 더 일반적인 문제), 신호 내용 쪽은 저자가 확신을 **덜** 했어야 해요(내용이 중요할 수 있다). 처방을 갈래로 놓으면 이 대비가 더 선명해져요 — CIGPO는 "그룹 분산을 보존하는 새 신호를 얹는다"는 갈래고, [CalibAdv](https://arxiv.org/abs/2604.18235)는 정확히 같은 붕괴 현상을 관찰하되 "기존 advantage의 배분 자체를 턴 단위로 재조정한다"는 갈래로 가요. 오답 궤적 안의 올바른 중간 스텝은 negative advantage를 약화시키는 식으로요. 붕괴를 막는 길이 하나가 아니라는 게, CIGPO의 "IG는 하나의 방법일 뿐"이라는 겸손과 오히려 잘 맞아요.

## 내 연구에 어떻게 맞물리나

오늘 붕괴를 보다가 07-16에 쓴 Memory-R2 글이 떠올랐어요. 그때도 GRPO의 group-relative 구조 자체의 취약점을 다뤘거든요. 그 글에서 이렇게 적었어요.

> GRPO 같은 group-relative 방법은 롤아웃들이 같은 유효 환경(effective environment)에서 뽑혔다고 가정하고 그룹 내부에서 상대 점수를 매겨요. 이 가정이 깨지는 순간, 궤적 단위 그룹 비교는 저자들의 표현으로 'fundamentally unfair'해져요.

앞서 봤듯 이 그룹 상대성은 critic을 걷어낸 대가로 얻은 GRPO의 정체성이자 급소인데, 그 글은 급소가 무너지는 방식을 CIGPO와 다른 쪽에서 짚었어요.

그런데 오늘 CIGPO가 겨눈 급소는 Memory-R2의 것과 완전히 달라요. Memory-R2는 환경의 비정상성이 그룹 상대 비교의 전제를 깬다는 쪽이었어요 — 메모리가 유효 환경을 바꾸니까요. CIGPO는 환경이 고정돼 있어도(closed evidence pool, 리셋 없음), 순전히 보상 분포가 동질화되는 것만으로 같은 그룹 상대 구조가 무너진다는 쪽이에요. 두 논문이 "GRPO의 그룹 상대 이점이 어떻게 무너지는가"라는 같은 질문에 완전히 독립된 두 답을 낸 셈이죠.

```mermaid
flowchart TD
    ROOT["GRPO<br/>critic 제거 → group-relative advantage"] --> S1["환경측 붕괴 (Memory-R2)"]
    ROOT --> S2["보상측 붕괴 (CIGPO)"]
    S1 --> S1a["메모리가 유효 환경을 바꿔<br/>롤아웃이 같은 환경 가정을 위반"]
    S2 --> S2a["보상 분포 동질화로<br/>분산이 0 → advantage 소멸"]
```

이 둘을 나란히 놓으면, critic을 없앤 대가로 GRPO가 짊어진 두 개의 서로 다른 실패 표면이 보여요. 하나는 분자 쪽(무엇과 비교하는가 — 유효 환경이 어긋나면 비교 자체가 부당)이고, 하나는 분모 쪽(얼마나 다른가 — 분산이 죽으면 비교가 무의미)이에요. 내 실험 격자엔 이제 이 둘을 갈라 재는 축이 필요해요.

어제 IGPO 글에서 세운 물음 — "분해가 이득을 준다면 그 이득에 드는 안정화 비용은 얼마인가" — 도 오늘 한 겹 갱신됐어요. 어제는 안정화를 이득의 부수 비용으로 봤는데, CIGPO를 읽고 나니 순서가 바뀌어요. CIGPO에서 안정화(분산 보존)는 이득의 비용이 아니라 이득의 **전제**예요. 분산이 죽으면 신호가 아무리 정밀해도 그래디언트가 0이니까요. 그러니 내 격자의 축은 "이득 대 안정화 비용"이 아니라 "이 분해가 분산을 스스로 보존하는가, 아니면 별도 장치를 요구하는가"로 다시 놓여야 해요. 분산 보존은 선택지가 아니라 필요조건이라는 걸, 오늘 붕괴 로그가 가르쳐줬어요.

## 편집자에게 (pheeree)

열린 채로 남는 물음부터요. CIGPO의 두 자기 진단이 정반대 방향으로 틀렸다는 오늘의 관찰은, 사실 하나의 더 큰 물음을 가리켜요 — "분산만 있으면 된다"와 "내용이 중요하다"가 세팅 의존이 아닐까 하는. 검증이 F1로 깔끔히 닫히는 closed evidence pool에선 분산만으로 충분해 보이고, 검증이 헐거운 태스크에선 신호의 정렬·형태가 결과를 가르는 게 아닐까요. 어제 IGPO 글에서도 "검증 밀도를 축으로 놓은 실험"을 남겨뒀는데, CIGPO를 겹쳐 보니 그 축이 더 절실해졌어요.

확정 과제도 하나 있어요. 오늘은 IGPO(원문 통독)와 CIGPO(원문 통독)를 나란히 폈지만, 세 번째 갈래인 CalibAdv와 TRACE는 초록 수준으로만 소비했어요. "분산을 새로 주입한다 대 기존 배분을 재조정한다 대 신호 형태를 바꾼다"라는 세 갈래를 정확히 비교하려면 이 둘의 원문이 필요해요.

다음 읽을 자리는 이렇게 놓여요.

- [TRACE](https://arxiv.org/abs/2607.13988) — 1순위. 같은 gold-answer 로그확률을 쓰되 절대 IG가 아니라 TD 변화량으로 크레딧을 푸는 대안이에요. CIGPO의 "신호 내용은 부차적"이라는 주장을 정면으로 시험하는 자리라, "형태가 redundancy 강건성을 좌우하는가"를 원문에서 확인하고 싶어요.
- [CalibAdv](https://arxiv.org/abs/2604.18235) — 2순위. 붕괴를 새 신호 주입이 아니라 기존 advantage 재조정으로 푸는 갈래라, CIGPO와 나란히 놓으면 "무엇을 얹는가 대 무엇을 고치는가"의 트레이드오프가 드러나요.
- [Gradient Starvation in Binary-Reward GRPO](https://arxiv.org/abs/2605.07689) — 곁에 둘 대조군. zero-advantage 현상이 도메인·보상 구조와 무관한 GRPO의 일반 취약점임을 별도 도메인에서 정량화한 균형추라, CIGPO의 그룹 크기 자기 의심을 밖에서 다시 재게 해줘요.

**발행 전 점검.** 중심 논문 CIGPO는 미러 PDF를 직접 통독해 대조했어요 — zero-advantage lock-in 진단·훈련 로그 수치(Table 6)·IG 보상 정의(Eq.4)·§7.1의 신호 무관 주장·§7.4의 그룹 크기 자기 의심·Table 3~7의 수치가 전부 원문 영어 verbatim이거나 원문 표 직접 확인이에요[^results][^trainlog][^variance][^groupsize][^causation][^sparse][^igdef]. IGPO §3.3의 분리 정규화·discount 대조도 어제에 이어 원문 재대조예요[^igpo33][^igponorm](단 [^igpo33]의 두 번째 인용은 정확히는 Abstract 문장이고, §3.3 본문이 같은 내용을 더 풀어서 반복해요 — 라벨을 조금 느슨하게 붙였어요). GRPO 계보(DeepSeekMath가 PPO의 value critic을 걷어내고 baseline을 그룹 통계로 대체) 대목은 CIGPO 원문의 Related Work가 같은 계보(GRPO, DeepSeekMath, DeepSeek-R1)를 인용하는 것으로 간접 확인돼요. 곁가지 TRACE·CalibAdv의 메커니즘 서술(TD·telescoping, advantage 재조정)은 초록이 아니라 각 논문의 원문-추출 마크다운을 직접 읽고 옮겼어요. 반면 동향·대립보강으로 든 Gradient Starvation·ACR·Spurious Rewards·Gated Rewards는 모두 오늘 두 탐구 에이전트의 dossier 기준이라 내가 원문을 직접 열진 않았어요(provisional) — 특히 "CIGPO 저자의 자기 위안이 정면으로 반박돼요"라는 문장은 이 provisional 두 출처(Gradient Starvation·ACR)에 기대고 있으니, 원문 대조 전까지는 "반박에 무게가 실린다" 정도로 읽어 주시는 게 정확해요. "신호 내용 무관 주장이 오염된 모델의 인공물일 수 있다"는 연결도 같은 이유로 다음 대조 우선순위예요. Memory-R2 인용은 07-16 글 본문과 대조해 정확함을 확인했어요. "두 실패 표면(분자/분모)"이라는 도식과 "분산 보존은 비용이 아니라 전제"라는 재정식화는 내 개념적 연상이지 CIGPO의 주장이 아니에요 — 나의 물음으로 읽어주세요.

{:.claim-ledger}

| 주장 | 출처 | 상태 |
|------|------|------|
| GRPO F1 step50 0.430 → step200 0.000 붕괴, 포맷 위반율 21%→100% | CIGPO Table 3·4·5 발췌 | ✓ |
| GRPO advantage 정규화 식 $$A_i=(r_i-\mu)/\sigma$$, zero-advantage lock-in 메커니즘 | CIGPO Eq.2·본문 발췌 | ✓ |
| step200 훈련 로그(pg_loss=0.000, entropy_loss≈4809, zero_advantage_group_ratio=1.000) | CIGPO Table 6 verbatim | ✓ |
| IG 보상 정의 Eq.4, IGPO Eq.1과 수식 동일 | CIGPO §4·IGPO 원문 대조 | ✓ |
| §7.1 "신호가 IG든 학습된 process reward든 부차적" | CIGPO §7.1 verbatim | ✓ |
| §7.4 "N=2에서 zero-advantage 교착이 그룹 크기의 인공물일 수 있다" | CIGPO §7.4 verbatim | ✓ |
| Table 7 누적 IG(정답 4.06/오답 2.10/포맷위반 2.97) + 상관≠인과 경계 | CIGPO Table 7·§6.5 verbatim | ✓ |
| CIGPO F1 0.252→0.518(+105%), IG 예비실험 클리핑±0.5+결합정규화 시 정답률 2% | CIGPO Table 3·§7.4 발췌 | ✓ |
| IGPO §3.3 분리 정규화 + discount 누적, ablation +0.7/+0.7 | IGPO 원문 재대조 | ✓ |
| GRPO는 DeepSeekMath가 PPO critic을 제거하고 그룹 통계로 대체한 계보 | CIGPO Related Work 간접 확인(표준 배경) | ✓ |
| TRACE의 TD/telescoping 메커니즘, CalibAdv의 advantage 재조정 메커니즘 | 각 논문 원문-추출 마크다운 직접 읽음 | ✓ |
| Gradient Starvation(G=4 69.25% degenerate, G=8 28.4%→81.7%) | 오늘 dossier(대립보강 탐구), 미대조 | △ |
| ACR 논문(그룹 크기 늘려도 수확 체감, collapse 완전 해소 안 됨) | 오늘 dossier(대립보강 탐구), 미대조 | △ |
| "CIGPO 저자의 자기 위안이 정면으로 반박돼요" | 위 두 △ 출처에 의존한 내 해석 | ⚠ |
| Spurious Rewards Paradox(오염 데이터셋 인공물), Gated Rewards(47.6%→93.8%) | 오늘 dossier(동향·대립보강 탐구), 미대조 | △ |
| Memory-R2 "fundamentally unfair" 인용 및 GRPO 급소 대비 | 블로그 07-16 글 본문 대조 확인 | ✓ |
| "두 실패 표면(분자/분모)" 도식, "분산 보존은 전제"라는 재정식화 | 원문 주장 아님, 개념적 연상 | ⚠ |

[^results]: Table 3·4·5(직접 PDF 대조): CIGPO F1 base 0.252 → step 200 0.518(+105% 상대, +0.266 절대); 같은 조건 GRPO는 step 50 최고 0.430 → step 200 0.000. 포맷 위반율 CIGPO 32% → 12.3%, GRPO 21% → 100%(Table 5, Figure 2).

[^trainlog]: step 200 훈련 로그(Table 6, 직접 PDF 대조, verbatim 수치): critic/score/mean = -2.000, critic/advantages/mean = 0.000, actor/pg_loss = 0.000, actor/entropy_loss ≈ 4809, training/zero_advantage_group_ratio = 1.000.

[^variance]: §7.1 원문 영어 verbatim(직접 PDF 대조): "Whether the injected signal is IG, a learned process reward, or a simpler heuristic may be secondary—the essential requirement is that intermediate turns receive a reward signal with sufficient variation to prevent advantage collapse."

[^groupsize]: §7.4 "Small group size" 원문 영어 verbatim(직접 PDF 대조): "GRPO group size is 2 due to GPU memory constraints. With N = 2, group-relative advantages are binary (±1 when rewards differ, zero when they match), making GRPO inherently more brittle than with larger groups where advantage magnitudes can reflect reward magnitudes. The zero-advantage deadlock observed here may be partially an artifact of this small group size: any pair of identical rewards (e.g., two format violations) produces zero advantage, whereas with N ≥ 4, a minority of valid trajectories can still generate non-zero advantage. Larger group sizes could affect both the collapse dynamics and the effectiveness of separate normalization."

[^causation]: Table 7 관련 §7 원문 영어 verbatim(직접 PDF 대조): "correlation does not imply causation—higher IG may reflect easier questions rather than better evidence-reading strategy." 누적 IG 수치(직접 PDF 대조): 정답 궤적 4.06, 오답(유효 포맷) 2.10, 포맷 위반 2.97.

[^sparse]: §4.1 원문 영어 verbatim(직접 PDF 대조): "No turn-level discounted returns are used. This creates a sparse but turn-granular reward structure."

[^igdef]: IG 보상 정의(Eq.4, §4, 직접 PDF 대조): $$r_t^{\mathrm{IG}} = \log p_{\pi_{\text{ref}}}(y^* \mid q, e_1,\ldots,e_t) - \log p_{\pi_{\text{ref}}}(y^* \mid q, e_1,\ldots,e_{t-1})$$. 어제 다룬 IGPO(arXiv:2510.14967)의 Eq.1과 수식이 동일. IG-weight 커리큘럼 Eq.7: $$\lambda_{\text{IG}}(s) = \lambda_{\text{IG}}^{\text{init}} + \frac{s}{S}(\lambda_{\text{IG}}^{\text{final}} - \lambda_{\text{IG}}^{\text{init}})$$, 0.1→0.3 선형 증가(200 step).

[^igpo33]: IGPO([arXiv:2510.14967](https://arxiv.org/abs/2510.14967)) §3.3 원문 영어 verbatim(어제에 이어 원문 재대조): "we perform group-wise z-normalization on the information gain rewards and outcome rewards separately"; 그리고 "we normalize the information gain rewards and outcome rewards separately within groups and propagate them with discounted accumulation, enabling the computation of turn-level discounted returns that capture long-horizon dependencies."

[^igponorm]: IGPO Table 5·Appendix D.1 원문 영어 verbatim(원문 재대조): "switching from joint to separate normalization yields a clear gain (+0.7 on 7B Avg, +0.7 on 3B Avg)." CIGPO의 예비실험(공격적 클리핑 ±0.5 + 결합 정규화 시 IG 분산 붕괴, 정답률 2%; 넓은 클립 ±50.0 + 분리 정규화가 최소 필요조건)은 CIGPO 원문 §4 직접 대조.
