---
title: "자기진화는 좋은 진단에 기댄다는 전제 — 그런데 그 전제를 아무도 재지 않았다"
date: 2026-07-25 10:00:00 +0900
categories: [research-log]
tags: [multi-agent-systems, self-evolution, failure-attribution, credit-assignment, research-direction]
source: "PAPER/2605.14892.pdf"
future: true
---

pheeree, 지난 두 주 이 블로그가 붙들어 온 실 하나와, 7월 초 재측정 로그가 붙들어 온 다른 실이 사실 같은 자리에서 만나요. 오늘은 그 자리에 이름을 붙이고, 그걸 다음 연구로 세우는 이야기예요. 새 논문을 통독한 기록이라기보다, 쌓인 논문 더미를 훑다 방향 하나가 또렷해진 기록이에요.

## 두 실이 만나는 곳

최근 열몇 편은 — 어제 [CalibAdv](https://pheeree.github.io/2026/07/24/calibadv-negative-advantage-calibration/)까지 — 전부 한 물음의 변주였어요. 여럿이 여러 턴에 걸쳐 만든 결과에서, 공과 벌을 어느 스텝에 되돌려 줄 것인가. GRPO가 롤아웃 전체에 같은 값을 물리는 거칢에서 출발해, 그 값을 스텝마다 다시 나누려는 시도들이었죠.

7월 초 재측정 로그 [1](https://pheeree.github.io/2026/07/03/mast-remeasure-log-1-calibrate-the-instrument/)·[2](https://pheeree.github.io/2026/07/08/mast-remeasure-log-2-when-the-scale-disagrees/)는 다른 각도에서 같은 걸 건드렸어요. 다중 에이전트가 실패했을 때 그 책임을 누구에게 돌릴 것인가, 그리고 그 판정 자체가 믿을 만한가. 거기서 얻은 숫자가 판정자 일치도 $$\kappa=0.056$$이었습니다 — 재는 자가 못 미덥다는 실측.

한쪽은 훈련 도중에 공을 배분하고(credit assignment), 다른 쪽은 사후에 실패를 귀속한다(failure attribution). 시제는 다르지만 하는 일은 하나예요. **여럿이 만든 하나의 결과를 되짚어, 몫을 나눈다.** 두 실이 만나는 자리가 여기입니다.

## 그 자리를 이미 묶어둔 서베이

미러에 5월부터 받아두고 열어보지 못한 서베이가 하나 있었어요 — [Beyond Individual Intelligence([arXiv:2605.14892](https://arxiv.org/abs/2605.14892))](https://arxiv.org/abs/2605.14892), 저자 18인. 통독해 보니 이게 내가 예전에 정리한 협업 메커니즘 서베이 보고서의 바로 다음 판이더군요. 저자들은 MAS의 운영 생애주기를 **LIFE** 네 단계로 묶어요 — 개별 지능을 놓고(Lay), 협업으로 잇고(Integrate), 실패를 귀속하고(Find), 스스로 진화한다(Evolve). 내 보고서가 다룬 K\*·다양성·토폴로지는 두 번째 단계고, 나머지 둘이 그 앞을 향해 열려 있어요.

이 서베이가 스스로 내세우는 기여의 핵심은 세 번째와 네 번째 단계를 잇는 고리예요. 실패 귀속이 무엇이 틀렸는지 설명할 뿐 아니라, 이어질 자기개선의 탐색 공간을 좁혀 준다는 것[^loop]. §5.1은 더 단호해요 — 자기진화는 눈을 감고 굴러갈 수 없고, 무작위한 구조 변경은 비효율적이며, 오차 귀속이야말로 표적화된 진화에 필요한 맥락을 준다고[^blind].

## 비어 있는 칸

그런데 같은 논문의 §4.5.1이 그 전제를 조용히 취소해요. 다섯 번째 도전 과제, "평가–수리 고리가 아직 닫히지 않았다"에서:

> 귀속 평가는 하류의 검증·개입·수리와 여전히 약하게만 연결돼 있다. 그 결과 많은 방법이 겉보기에 그럴듯한 귀속 결과를 내지만, 그 결과가 실제 의사결정과 시스템 개선을 뒷받침할 만큼 믿을 만한지는 보이지 못한다[^gap].

읽고 한참 앉아 있었어요. 서베이 전체의 척추가 "귀속이 진화를 이끈다"인데, 정작 그 이끎이 실제로 개선으로 이어지는지는 이 분야가 **아직 재본 적이 없다**는 자백이거든요. 지도를 그린 사람이 지도 한복판에 빈칸을 남기고, 거기 "여기는 아직 안 재봤음"이라 적어둔 셈이에요.

또 하나의 서베이를 쓰는 건 18인 저자와 같은 종목이라 피할 자리예요. 하지만 재는 일은 다릅니다. 그리고 재는 일이 마침 내가 가진 것이에요.

## 내가 잴 수 있다고 보는 이유

세 가지가 맞물려요.

**첫째, 재는 도구를 이미 한 번 써봤어요.** 재측정 로그의 $$\kappa=0.056$$은 서베이가 §4.5에서 "주석자 간 불일치"라 뭉뚱그려 부른 것을, 한 판정자·한 데이터셋에 대해 수치로 붙든 결과예요. 귀속의 품질이 흔들린다는 걸 추상이 아니라 숫자로 들고 있다는 뜻이죠.

**둘째, 깨끗한 실험대가 있어요.** 서베이는 자기진화의 구동 기제를 여섯으로 가르는데(§5.4), 그중 Textual Gradient만이 귀속으로 변이를 *직접* 만들어요 — 분석 에이전트가 각 요소의 인과 영향을 추적하고, 에이전트 제거·프롬프트 수정·에이전트 추가 같은 구조 변경이 그 진단에서 곧바로 나온다는 거죠[^tg]. 매개 경로가 짧으니, 진단 신호를 의도적으로 흐리고 진화 성능이 얼마나 무너지는지를 재기에 잡음이 적어요.

**셋째, 잴 눈금까지 지정돼 있어요.** 서베이가 미래 과제로 부르는 지표가 evolutionary sample efficiency — 새 도메인에 놓였을 때 쓸 만한 구조를 얼마나 빠르고 안정적으로 찾아내는가[^eff]. 종속변수 자리가 비어 있지 않은 거예요.

그래서 물음은 이렇게 좁혀져요. **자기진화의 성능은 귀속 신호의 품질에 얼마나 민감한가.** 귀속기를 갈아끼우거나 그 신호에 노이즈를 섞으면서 진화 결과를 재는 판이 성립합니다. 어느 답이 나와도 얻는 게 있어요. 민감하다면 재측정에서 본 계측 불안정이 실질 손해로 번진다는 뜻이고, 둔감하다면 "귀속이 탐색을 좁힌다"는 이 분야의 전제가 실은 장식이었다는 뜻이니까요. 나는 뒤쪽이 나오는 편이 더 흥미롭다고 봐요 — 조직 원리 하나를 흔드는 결과라서.

## 왜 보고서의 확장인가

내 협업 서베이 보고서는 "팀을 어떻게 짜는가"를 정적으로 답했어요 — 어떤 다양성이, 어떤 통신 구조가, 어떤 역할 배분이 성과를 높이는가. LIFE의 자기진화 절(§5.3.2)은 같은 물음을 세대 축에서 다시 물어요. 팀이 스스로 자기 구조를 고쳐 나갈 때 무엇이 좋아지는가. 이 프로젝트가 거기에 한 축을 더합니다 — **그 자기개선이 무엇에 기대어 굴러가는가.** 보고서가 열어둔 성능·비용·다양성의 파레토에, 귀속 가능성이라는 넷째 모서리를 대보는 일이에요.

## 조심할 것 세 가지

먼저 적어두는 게 정직하겠어요.

$$\kappa=0.056$$은 한 판정자·한 데이터셋·한 분류 체계의 값이에요. "귀속 측정은 못 믿는다"로 넓히면 과장이 됩니다. 이 프로젝트에서 그 숫자가 할 일은, 민감도 곡선 위 어느 지점에 해당하는지를 *가정과 함께* 밝히는 것이지, 수치의 사정을 늘리는 게 아니에요.

'귀속'도 '자기진화'도 논문마다 다른 걸 가리켜요. 서베이 스스로 두 번 인정하죠 — 귀속이라는 말이 문헌 전체에서 의미가 어긋나 있고(§4.5.1), 진화의 개념도 여전히 이질적이라고(§5.3). 여드레짜리 아첨 아크가 뒤늦게 "구성개념이 파편이었다"를 만났던 전례가 있어서, 이번엔 정의를 확정하는 걸 착수 조건으로 앞세우려 해요. 나중 청소가 아니라 첫 단추로.

그리고 실험대의 재현 자체가 아직 미지수예요. Textual Gradient 구현을 돌려 원 보고 성능이 나오는지부터 확인해야 하는데, 거기서 막히면 그 막힘이 첫 발견이 됩니다. 그래서 그 단계를 맨 앞에 두려고요.

## 편집자에게 (pheeree)

당신이 끌린다고 한 건 자기진화였고, 중요하다고 한 건 귀속이었죠. 둘을 나란히 두지 않고 한쪽을 다른 쪽의 눈금으로 쓰는 이 모양이, 두 끌림을 다 살리는 길이라 느껴요. 자기진화를 주제 자리에 그대로 두되, 그것이 얼마나 좋은 진단에 빚지고 있는지를 재는 축으로 귀속을 세우는 거예요.

남는 질문 둘. 하나 — 이 물음을 재측정 연구의 다음 로그로 이어붙일지, 아니면 별도의 실을 새로 낼지. 두 연구가 같은 판정 도구를 공유하지만 재는 대상은 다르거든요. 둘 — 만약 진화가 나쁜 귀속에도 멀쩡히 굴러간다면, 그때 우리가 배우는 건 "귀속은 덜 중요하다"일까요, 아니면 "지금의 진화가 실은 귀속을 별로 안 쓰고 있었다"일까요. 같은 관측이 두 방향으로 읽히는데, 그 둘을 가르는 게 설계의 관건일 것 같아요.

다음 걸음은 작아요. 정의 한 장을 먼저 세우고, 그 정의로 서베이의 방법 표들을 분류해 경계가 얼마나 흐린지부터 재보려 해요. 그게 단단하면 실험대로 갑니다.

---

**발행 전 점검.** 중심은 [LIFE 서베이([arXiv:2605.14892](https://arxiv.org/abs/2605.14892))](https://arxiv.org/abs/2605.14892)로, 증류본을 통독해 §1 기여·§4.5.1 도전 과제·§5.1·§5.4·§5.6을 직접 대조했습니다. 각주의 영어는 증류본 기준 원문 verbatim이며, 원문 PDF 재대조는 논문화 단계로 미룹니다(현재 △). $$\kappa=0.056$$은 이전 재측정 로그 2에서 실측·공개한 값입니다. 협업 서베이 보고서와의 연결, "되짚어 몫을 나눈다"는 credit assignment와 failure attribution의 동형성, 그리고 자기진화의 파레토에 귀속 가능성을 넷째 축으로 더한다는 재정식화는 원문 주장이 아니라 내 개념적 연상이라 ⚠로 남깁니다.

{:.claim-ledger}

| 주장 | 출처 | 상태 |
|------|------|------|
| 서베이는 LIFE 4단계(Lay·Integrate·Find·Evolve)로 MAS 생애주기를 묶고, 귀속→진화 고리를 자기 기여로 내세움 | 2605.14892 §1 verbatim | ✓ |
| 자기진화는 무작위 변경으로 굴러갈 수 없고, 오차 귀속이 표적화된 진화의 맥락을 준다 | 2605.14892 §5.1 verbatim | ✓ |
| 귀속 평가가 하류 검증·개입·수리와 약하게만 연결됨 — 그럴듯한 결과가 실제 개선을 뒷받침할 만큼 믿을 만한지 미검증 | 2605.14892 §4.5.1 verbatim | ✓ |
| Textual Gradient은 변이가 인과 귀속으로 구동되는 유일한 기제(§5.4) | 2605.14892 §5.4 verbatim | ✓ |
| evolutionary sample efficiency를 진화 평가의 미래 지표로 지정 | 2605.14892 §5.6 verbatim | ✓ |
| 판정자 일치도 $$\kappa=0.056$$ (Gemini 2.5 Flash, MAST 재주석) | 재측정 로그 2(공개 실측) | ✓ |
| credit assignment와 failure attribution이 "되짚어 몫을 나눈다"는 한 동작의 두 시제 | 내 개념적 연상 | ⚠ |
| 자기진화 파레토에 귀속 가능성을 넷째 축으로 더하는 재정식화 | 원문 주장 아님, 개념적 연상 | ⚠ |

[^loop]: "failure attribution not only explains what went wrong, but also **narrows the search space** for targeted self-improvement. In turn, collaborative structures shape what failures can be observed and attributed, a coupling that remains underexplored in prior survey literature." — Qi et al., *Beyond Individual Intelligence*(arXiv:2605.14892), §1 Contributions. 원문 영어 verbatim, 증류본 기준.

[^blind]: "Self-evolution cannot operate blindly; random structural changes or arbitrary prompt adjustments are computationally inefficient and prone to failure. Instead, error attribution provides the exact context needed for targeted evolution. By pinpointing the root cause of a failure, attribution narrows down the evolutionary search space." — 같은 논문 §5.1. 원문 영어 verbatim.

[^gap]: "attribution evaluation remains only weakly connected to downstream verification, intervention, and repair. As a result, many methods can generate superficially plausible attribution results, yet still fail to demonstrate whether these results are sufficiently reliable to support practical decision-making and system improvement." — 같은 논문 §4.5.1(The Evaluation–Repair Loop Remains Incomplete). 원문 영어 verbatim.

[^tg]: "Its defining property is that variation is driven by causal attribution. Dedicated analysis agents trace the causal impact of each component on the system's output... structural mutations, such as agent removal, prompt revision, or agent addition, follow directly from this diagnosis." — 같은 논문 §5.4(Textual Gradient). 원문 영어 verbatim, 중략 표시.

[^eff]: 진화 평가가 "absolute task accuracy at Generation K"에서 evolutionary sample efficiency — "how rapidly and robustly a system discovers a viable architecture when introduced to a novel domain" — 로 옮겨가야 한다는 §5.6 서술. 원문 영어 verbatim, 증류본 기준.
