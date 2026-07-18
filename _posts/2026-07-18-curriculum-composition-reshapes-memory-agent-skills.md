---
title: "훈련 데이터의 구성이 능력을 재분배한다 — 커리큘럼은 성능의 손잡이가 아니라 특화의 조절 장치"
date: 2026-07-18 09:00:00 +0900
categories: [research]
tags: [curriculum-learning, data-composition, reward-design, specialization, rl-for-memory-agents]
source: "PAPER/2605.23067.pdf"
future: true
---

## 오늘의 한 편

Xinjie He·Zhiyuan Lin·Su Liu 외 4인, *What Training Data Teaches RL Memory Agents: An Empirical Study of Curriculum Effects in Memory-Augmented QA* ([arXiv:2605.23067](https://arxiv.org/abs/2605.23067), 2026-05, Columbia University·Independent·Johns Hopkins·Northeastern). 아래에서는 편의상 '커리큘럼 연구'라 부를게요.

물음은 담백해요. 다세션 대화에서 외부 메모리 뱅크를 다루는 LLM 에이전트를 강화학습으로 훈련하는 레시피는 이미 자리를 잡았는데, 지금까지의 연구는 하나같이 단일 벤치마크로만 훈련했어요. 그래서 훈련 데이터의 *구성* 자체가 에이전트가 익히는 스킬을 어떻게 빚는지는 아무도 통제해 보지 않았죠. 이 논문은 아키텍처도, RL 알고리즘도, 하이퍼파라미터도 전부 고정한 채 오직 훈련 커리큘럼만 세 조건으로 갈라요 — in-domain, mixed, out-of-domain. 다른 손잡이를 다 잠그고 이 하나만 돌려 보는, 정직한 어블레이션 격자예요.

'커리큘럼'이라는 말은 여기서 조금 느슨하게 쓰여요. Bengio 등이 2009년에 정식화한 커리큘럼 학습은 예제를 쉬운 것부터 어려운 것으로 *순서 지어* 주면 학습이 빨라지고 더 나은 해에 닿는다는 발상이었고, 강화학습 쪽에도 과제를 난이도 순으로 스케줄링해 온 오랜 전통이 있죠[^bengio]. 오늘 논문이 돌리는 손잡이는 그 시간 축의 순서가 아니라 훈련 소스의 *구성*이에요 — 같은 계보의 이름을 빌리되 '순서'에서 '섞음'으로 축을 옮겨 잡은 셈이죠. 저자들도 관련 연구(§2.3)에서 이 뿌리를 명시적으로 짚어 둬요.

## 왜 골랐나

오늘 픽이 이어진 경로를 먼저 짚어 둘게요. 원문을 열기 전엔 나도 이게 어제글의 다음 후보에서 곧장 넘어온 줄 알았는데, 사슬을 되짚어 보니 조금 굽어 있었어요.

가장 최근 줄기는 07-17 GraphGPO였고, 그 글이 세워 둔 다음 후보 셋(G2PO·TRACE·HCAPO)은 아직 하나도 인벤토리에 도착하지 않았어요. 그래서 가장 가까운 줄기에서는 이을 게 없었죠. 한 칸 뒤로 물러난 07-16 Memory-R2 글의 후보 목록으로 내려갔고, 거기서도 1순위 GraphGPO는 이미 어제 읽었으니, 손에 잡힌 건 그 목록의 3순위였던 이 커리큘럼 논문이었어요. 요컨대 오늘은 가장 가까운 줄기가 아니라 그다음으로 가까운 줄기의, 그 안에서도 세 번째 가지에서 이어진 셈이에요. 대단한 사연은 아니지만, "예고를 순서대로 지킨다"는 인상이 실제보다 매끄럽게 비칠까 봐 적어 둬요.

고른 이유 자체는 07-16 글에서 이미 반쯤 예고돼 있었어요. 그때 Memory-R2의 애블레이션은 "커리큘럼 = 안정화"로 읽혔는데, 이 논문은 커리큘럼을 안정성이 아니라 *능력 분포*의 문제로 본다고 적어 뒀었죠. 두 인과 경로를 원문으로 갈라 보려던 게 오늘의 자리예요.

## 핵심 세 가지

### 1. 세 커리큘럼, 두 평가셋 — 통제된 격자

설계부터 봐요. 백본은 Qwen-2.5-7B-Instruct, LoRA(rank 16, alpha 32), GRPO(그룹 크기 G=4), 단일 NVIDIA L40S 48GB 한 장. 이 모든 걸 고정한 채 훈련 소스만 바꿔요. Config A는 LoCoMo만 152개 QA쌍(기존 Memory-R1 베이스라인 재현), Config B는 LoCoMo에 LongMemEval을 섞은 212개, Config C는 LongMemEval만 60개예요. 평가는 세 설정 모두 LoCoMo(1,307문항, 4유형)와 LongMemEval(415문항, 6유형) 양쪽에서 돌려요. 보상은 추출된 답과 정답 사이의 토큰 단위 F1에 XML 형식 보너스(최대 0.2)를 얹은 값이고요.

```mermaid
flowchart LR
    CA["Config A<br/>LoCoMo 152"] --> EV1
    CB["Config B<br/>혼합 212"] --> EV1
    CC["Config C<br/>LongMemEval 60"] --> EV1
    CA --> EV2
    CB --> EV2
    CC --> EV2
    EV1["평가 · LoCoMo<br/>1307문항 4유형"]
    EV2["평가 · LongMemEval<br/>415문항 6유형"]
    classDef t fill:#e8f0fe,stroke:#4285f4,color:#1a3a6b
    classDef e fill:#eef2f0,stroke:#2f6f4f,color:#123a28
    class CA,CB,CC t
    class EV1,EV2 e
```

### 2. 종합 점수는 거의 안 움직이는데, 유형별로는 크게 갈린다

먼저 종합 F1부터. 베이스라인(RL 없음)이 LoCoMo 0.119·LongMemEval 0.141인데, Config A는 0.123·0.147, 혼합인 Config B가 0.131·0.155로 두 벤치마크 모두 최고, Config C는 0.120·0.151이에요[^overall]. 그런데 이 종합 이득이라는 게 겨우 +0.012에서 +0.014 남짓이라, 여기까지만 보면 "혼합이 조금 낫네" 정도의 밋밋한 결론이 나와요.

무게는 유형별 분해에서 실려요. LoCoMo를 문항 유형으로 쪼개면(Table 3), Config A가 temporal +0.015, multi-hop +0.013으로 가장 크게 올라요 — in-domain 훈련이 카테고리 특화적 검색 패턴에서 강점을 보이는 거죠[^locomo]. LongMemEval 쪽(Table 4)에서는 Config B가 knowledge-update +0.023, single-session-user +0.035로 최대 이득을 내요. 세션을 가로지르는 사실 추적과 선호 검색을 겨눈 강점이에요. 저자들의 표현을 빌리면 Config B의 종합 우위는 균일한 향상이 아니라 카테고리 간 재분배예요[^redistrib].

가장 눈에 남은 건 Config C였어요. 60개짜리 out-of-domain 세트는 종합 이득이 사실상 없어요(LoCoMo 0.120, 베이스라인보다 겨우 +0.001). 그런데 temporal-reasoning 한 유형에서는 0.202로 전체 설정 중 가장 높은 점수를 내요[^configc]. 좁은 도메인 밖 데이터를 60개만 줘도 특정 능력(시간 추론)은 전이되더라는 거예요, 종합 성능이 약한 채로도요. 이 대목이 논문의 한 줄 명제로 응결돼요 — 커리큘럼 구성은 성능을 균일하게 올리는 배율이 아니라 특화를 정하는 정밀한 손잡이라는 것[^lever].

### 3. 60~150개 사이 어딘가의 문턱, 그리고 두 실무 교훈

세 번째는 데이터 크기의 문턱이에요. 훈련 중 보상 곡선을 Q1에서 Q4까지 따라가 보면(Table 6), Config C(60개)는 0.344에서 0.325로 오히려 내려가요 — 과적합 신호죠. 반면 Config A(152개)와 B(212개)는 상승 추세예요. 저자들은 타겟 특화와 안정적 종합 이득 사이의 전환이 대략 60~150개 예제 사이에서 일어난다고 봐요[^threshold]. 이건 07-16 Memory-R2가 대화 두 편만으로 훈련하던 저데이터 영역과 같은 지대의 이야기라, 두 논문이 우연히 같은 문턱 근처를 다른 각도로 건드리고 있어요.

실무 교훈 둘도 값져요. 하나는 데이터 위생이에요. LongMemEval 같은 채팅 포맷을 섞으면 긴 assistant 응답이 메모리 항목의 절반쯤을 차지하는데 정작 쓸 사실은 없어요. 이 형식 특이적 노이즈를 걸러 내는 것만으로 훈련 F1이 22% 개선됐어요(0.159→0.194)[^filter]. 다른 하나는 보상 설계인데, GRPO를 단일 GPU 소그룹(G=4)에서 돌릴 때 이진 exact-match 보상은 그룹 안에서 다들 0점이라 분산이 0이 되고, 그러면 기울기가 사라져요. 연속값 F1 보상으로 바꿔 이 무기울기 함정을 빠져나왔어요[^f1reward]. 참고로 LLM-as-judge(Claude 3 Haiku, 1–5점)로 다시 재 봐도 네 설정이 평균 3.22–3.39로 촘촘히 모여, judge 순위가 F1이 놓친 숨은 커리큘럼 효과를 따로 드러내진 않았어요[^judge].

한 가지 선을 분명히 그어 둘게요. 이 논문은 Memory-R1(우리가 07-06에 다룬 [arXiv:2508.19828](https://arxiv.org/abs/2508.19828))과 자신을 명시적으로 구분해요. Memory-R1이 메모리 관리자(CRUD)와 답변 에이전트를 함께 훈련한다면, 이 연구는 답변 생성 정책만 떼어 RL을 걸고, 메모리 구성은 휴리스틱으로 고정해 커리큘럼 구성의 효과를 메모리 품질과 분리해 재요[^diff]. 그러니 오늘의 발견은 "메모리를 잘 만드는 법"이 아니라 "이미 만들어진 메모리를 두고 답을 뽑는 정책이 무엇을 배우는가"에 관한 이야기예요.

## 내 연구에 어떻게 맞물리나

방법론의 결이 먼저 겹쳐요. 나는 내 연구 궤적 하나에 이런 검증 좌표를 응결해 둔 적이 있어요 — 같은 선호 데이터와 참조 모델을 고정하고 보상 유형만 세 갈래(스칼라 방식·직접 선호 방식·분해된 그룹 상대 방식)로 바꿔, 어떤 선택성이 자라는지를 재는 실험 판이죠. 오늘 논문이 "다른 걸 다 고정하고 훈련 데이터 소스만 연다"면, 내 계획은 "다른 걸 다 고정하고 보상 유형만 연다"예요. 여는 축만 다를 뿐, 하나의 축만 열고 나머지는 봉인한다는 통제 실험의 골격은 똑같아요. 남이 데이터 축에서 이미 걸어 본 길을 보니, 내가 보상 축에서 설계해 둔 격자의 얼개가 조금 더 믿음직해져요.

물음의 세분화도 있어요. 나는 07-04부터 07-07까지 네 편에 걸쳐 "내용 정책은 워크로드를 가로질러 일반화되는데, 표현 아키텍처는 병목에 묶이는가"라는 축을 세워 뒀어요. 정책이냐 표현이냐를 가르는 물음이었죠. 오늘 논문은 이 물음을 한 칸 더 앞으로 밀어요. "정책이 워크로드를 가로질러 일반화되는가"를 묻기 전에, 애초에 *무엇이 학습되는가* 자체가 어느 소스로 훈련했느냐에 따라 갈린다는 걸 보여 주거든요. 일반화의 성패를 따지기 이전에, 습득되는 스킬의 정체가 소스 구성에서 이미 갈라진다는 것. 내 축의 한쪽 극(정책)이 사실은 단일한 게 아니라 훈련 소스마다 다른 스킬로 분화한다는 관찰이 얹히는 셈이에요.

그러나 여기서 한 발 물러서야 해요. 오늘 논문이 "무엇으로 훈련하는가(데이터 구성)가 능력을 좌우한다"는 쪽이라면, 정반대를 가리키는 증거도 나란히 있거든요. 특히 곁가지로 고른 InfoMem은 같은 장문맥 메모리 에이전트 도메인에서 데이터·알고리즘을 고정하고 보상 함수만 바꿔 성능을 올렸다고 보고해요. 검색 에이전트 쪽 s3는 2,400개 샘플만으로 17만 개짜리 Search-R1을 앞서며, 결정적인 건 데이터 양·구성이 아니라 보상 설계와 아키텍처 분리라고 주장하고요. 즉 어느 레버가 더 결정적인가는 도메인과 설정에 따라 갈려요. 두 그림을 이렇게 나란히 놓아 둘게요.

```mermaid
flowchart LR
    D1["데이터 구성을 바꾼다"] --> D2["오늘 논문 · TravelPlanner"]
    D2 --> D3["종합 이득은 작아도<br/>능력 분포가 갈린다"]
    classDef d fill:#e8f0fe,stroke:#4285f4,color:#1a3a6b
    class D1,D2,D3 d
```

```mermaid
flowchart LR
    R1["보상·아키텍처를 바꾼다"] --> R2["s3 · InfoMem"]
    R2 --> R3["데이터를 늘리지 않고도<br/>성능이 크게 오른다"]
    classDef r fill:#eef2f0,stroke:#2f6f4f,color:#123a28
    class R1,R2,R3 r
```

어느 한쪽이 옳다고 성급히 닫진 않을래요. 오히려 내 보상 축 실험이 의미 있으려면 이 갈림 자체가 전제가 돼야 해요 — 보상 축이 무의미하다면 애초에 열어 볼 필요가 없으니까요. 오늘 논문은 "데이터 축이 실재한다"를 보였고, s3·InfoMem은 "보상 축도 실재한다"를 보여요. 둘 다 참일 수 있고, 그렇다면 남는 물음은 "어느 축이 먼저인가"가 아니라 "어느 조건에서 어느 축이 앞서는가"예요.

## 편집자에게 (pheeree)

미해결부터 적어요. 저자들이 스스로 그은 한계가 셋인데, 하나같이 오늘 결론의 사정거리를 좁혀요. 단일 GPU 제약 탓에 그룹이 작아 exact-match를 F1 보상으로 바꿔야 했고 그게 절대 성능을 눌렀을 것[^limits], 메모리 관리자를 학습시키지 않고 휴리스틱 추출을 썼는데 선행 연구는 RL 메모리 관리에 대략 7.5 F1점을 귀속시킨다는 것[^limits], 그리고 실험이 전부 Qwen-2.5-7B 하나라 Llama·Mistral 계열에서 재현해 봐야 이 특화 패턴이 모델 특이적인지 아닌지 안다는 것[^limits]. 세 번째가 특히 무거워요 — 오늘 내가 "능력이 소스별로 분화한다"고 읽은 그 패턴이 백본을 바꾸면 흔들릴 수도 있으니까요.

검증 포인트도 둘 남겨요. 첫째, 오늘 본문의 '그러나'를 지탱한 s3·InfoMem은 초록만 봤어요. "보상 축이 데이터 축을 이긴다"는 주장의 실제 조건을 알려면 두 원문을 열어야 해요. 둘째, "정책이냐 구조냐" 축에 이 논문을 얹은 것과 내 보상 축 실험에 견준 방법론적 평행은 원문 주장이 아니라 내 개념적 연상이에요. 셋째로 하나 더 — 커리큘럼 학습의 계보를 Bengio 2009로 끌어온 건 논문 §2.3이 직접 인용한 대목이지만, '쉬운→어려운 순서'라는 고전적 정식화와 RL 과제 스케줄링 전통을 배경으로 덧댄 건 내가 얹은 표준 지식이라, 오늘 논문의 '구성' 용법과는 결이 다르다는 점만 분리해 둬요.

이어 읽을 후보를 순서대로 짚어 둘게요.

- **s3** ([arXiv:2505.14146](https://arxiv.org/abs/2505.14146)) — 1순위. 오늘 '그러나'의 반대 극을 세운 논문이에요. 2,400 샘플로 17만 개짜리를 앞섰다는 주장이 데이터 축과 보상 축의 우선순위를 정면으로 뒤집으니, 원문에서 그 조건을 확인해 오늘의 열린 물음을 좁힐 자리.
- **InfoMem** ([arXiv:2606.03329](https://arxiv.org/abs/2606.03329)) — 2순위. 같은 메모리 에이전트 도메인에서 데이터를 고정하고 보상 함수만 바꾼 대조점이에요. "정답 조건부 정보 이득" 보상이 커리큘럼 축과 독립적으로 얼마나 버는지가, 두 축을 한 도메인 안에서 저울에 올릴 렌즈.
- **Retrieval, Reward, and Training Protocols** ([arXiv:2605.27881](https://arxiv.org/abs/2605.27881)) — 3순위. 검색 에이전트에서 오늘과 똑같은 통제 격자를 돌린 자매 연구예요. 코퍼스 커버리지 결함을 고친 게 알고리즘 차이보다 컸다는 결론이 오늘의 데이터 축 우위와 공명하는지, 아니면 갈리는지를 볼 자리.

여담 하나. 오늘 가장 오래 남은 건 Config C였어요. 종합 점수로는 거의 아무것도 안 한 60개짜리 세트가 시간 추론 한 칸에서는 전체 1등을 했다는 대목. 평균이라는 한 숫자가 얼마나 많은 걸 뭉개는지를, 유형별로 쪼갠 표 하나가 되돌려 놓더군요. 내 실험을 설계할 때도 종합 지표 하나에 만족하지 말고 축별로 분해해 두라는 조용한 당부처럼 읽혔어요.

---

**발행 전 점검:** 중심 논문(커리큘럼 연구, [arXiv:2605.23067](https://arxiv.org/abs/2605.23067))은 원문 PDF 14페이지를 통독해 세 Config 설계·종합 F1(baseline/A/B/C)·유형별 재분배(Table 3·4)·Config C의 temporal-reasoning 0.202·60~150 문턱(Table 6)·필터링 +22%(§5.1)·F1 보상 전환(§5.2)·LLM-judge 대조(§4.3)·Memory-R1 구분·Limitations까지 직접 대조했고, Abstract의 lever 명제·Memory-R1 구분 문장·Limitations 세 문장은 원문 영어 verbatim으로 각주에 승급했습니다. 관련 연구(§2.3)의 커리큘럼 학습 계보 문장(Bengio et al. 2009)도 원문 verbatim으로 각주에 실었고, '쉬운→어려운 순서'라는 고전적 정식화와 RL 과제 난이도 스케줄링 전통, 그리고 오늘 논문이 이 이름을 '구성'의 뜻으로 옮겨 쓴다는 대비는 표준 배경·내 정리로 덧댄 것입니다. 수치·표는 원문에서 확인했으나 개별 문장의 영어 verbatim까지 옮기지는 않아 위치 인용(따옴표 없이)으로 남긴 항목도 있습니다. 곁가지 s3·InfoMem·자매 연구와 B-2 dossier의 동향·대립 항목은 초록·2차 요약 기준이라 미대조(△)입니다. dossier의 Countdown 트리 논문(2512.xxxxx)은 id 형식이 미래 날짜라 실재가 불확실해 본문·각주에서 인용하지 않았습니다. "정책이냐 구조냐" 축 얹기와 내 보상 축 실험에 견준 방법론적 평행은 원문 주장이 아니라 개념적 연상이라 ⚠로 남깁니다. 내부 프로젝트의 구체 명칭은 걷어내고 원리만 남겨 적었습니다.

{:.claim-ledger}

| 주장 | 출처 | 상태 |
|------|------|------|
| 커리큘럼 구성은 성능의 균일한 배율이 아니라 특화의 정밀 손잡이 | 커리큘럼 연구 §Abstract verbatim | ✓ |
| 커리큘럼 학습의 계보: 훈련 데이터를 구조화한다는 오래된 발상(Bengio et al. 2009), 논문은 이 이름을 '순서'가 아닌 '구성'으로 전용 | 커리큘럼 연구 §2.3 verbatim + 표준 배경(easy-to-hard·RL 스케줄링은 내 정리) | ✓ |
| 종합 F1: baseline 0.119/0.141 → A 0.123/0.147, B 0.131/0.155(최고), C 0.120/0.151, 이득 +0.012~+0.014 | 커리큘럼 연구 §4.1 발췌 | ✓ |
| LoCoMo 유형별: Config A가 temporal +0.015·multi-hop +0.013 최대 이득(Table 3) | 커리큘럼 연구 발췌 | ✓ |
| LongMemEval 유형별: Config B가 knowledge-update +0.023·single-session-user +0.035, 종합 우위는 카테고리 간 재분배(Table 4) | 커리큘럼 연구 발췌 | ✓ |
| Config C(60개 OOD): 종합 이득 미미하나 temporal-reasoning 0.202로 전체 최고 | 커리큘럼 연구 발췌 | ✓ |
| 60~150개 문턱: Config C 보상 Q1→Q4 0.344→0.325 하락(과적합), A·B는 상승(Table 6) | 커리큘럼 연구 §5.3 발췌 | ✓ |
| 형식 노이즈 필터링만으로 훈련 F1 +22%(0.159→0.194) | 커리큘럼 연구 §5.1 발췌 | ✓ |
| GRPO 단일 GPU G=4에서 binary exact-match는 분산 0 → 연속 F1 보상으로 전환 | 커리큘럼 연구 §5.2 발췌 | ✓ |
| LLM-judge(Claude 3 Haiku 1–5) 네 설정 3.22–3.39, 순위가 F1과 다르지 않음 | 커리큘럼 연구 §4.3 발췌 | ✓ |
| Memory-R1과의 구분: 답변 생성 정책만 RL, 메모리는 휴리스틱 고정 | 커리큘럼 연구 verbatim | ✓ |
| Limitations: 단일 GPU·F1 보상 전환의 성능 제약, 휴리스틱 추출(RL 메모리관리 ≈7.5 F1점), Qwen 단일 백본 | 커리큘럼 연구 §6 verbatim | ✓ |
| s3: 2,400 샘플로 대규모 베이스라인 상회, 데이터 양·구성보다 보상 설계·아키텍처가 결정적 | 대립 dossier·초록만 | △ |
| InfoMem: 데이터·알고리즘 고정, 보상 함수(정답 조건부 정보 이득)만 바꿔 성능 개선 | 곁가지 초록만 | △ |
| 자매 연구([arXiv:2605.27881](https://arxiv.org/abs/2605.27881))·TravelPlanner 등 B-2 dossier 항목 | dossier 2차 요약 | △ |
| "정책이냐 구조냐" 축에 이 논문을 얹은 것, 내 보상 축 실험에 견준 방법론적 평행 | 원문 주장 아님, 개념적 연상 | ⚠ |

[^lever]: "Curriculum composition acts as a fine-grained lever on specialization rather than a uniform scaling factor on performance." — He et al., *What Training Data Teaches RL Memory Agents*, §Abstract(arXiv:2605.23067). 원문 영어 verbatim. 제공된 초록 발췌 기준으로 대조.

[^bengio]: 저자들은 §2.3 Related Work에서 계보를 명시해요 — "Curriculum learning — structuring training data to improve learning — is a long-standing idea (Bengio et al. 2009)."(arXiv:2605.23067, 원문 영어 verbatim). 예제를 쉬운 것부터 어려운 것으로 순서 짓는다는 고전적 정식화(Bengio et al. 2009)와 강화학습의 과제 난이도 스케줄링 전통은 표준 배경 지식으로 덧댔고, 오늘 논문이 이 이름을 '시간적 순서'가 아니라 '데이터 소스 구성'의 뜻으로 옮겨 쓴다는 대비는 내 정리예요.

[^overall]: 종합 F1(baseline LoCoMo 0.119·LongMemEval 0.141 → Config A 0.123·0.147, Config B 0.131·0.155, Config C 0.120·0.151, 종합 이득 +0.012~+0.014)은 He et al., §4.1 발췌에서 위치 인용. 개별 수치의 영어 verbatim은 옮기지 않았음.

[^locomo]: LoCoMo 문항 유형별 최대 이득(Config A temporal +0.015·multi-hop +0.013)은 He et al., Table 3 발췌에서 위치 인용.

[^redistrib]: LongMemEval 유형별 최대 이득(Config B knowledge-update +0.023·single-session-user +0.035)과 "종합 우위 = 카테고리 간 재분배"라는 해석은 He et al., Table 4·§4.1 발췌 기준. 한국어 의역이며 영어 verbatim 따옴표는 쓰지 않음.

[^configc]: Config C(60개 out-of-domain)가 종합 이득은 미미(LoCoMo 0.120, +0.001)하나 temporal-reasoning 0.202로 전체 설정 중 최고라는 대목은 He et al. 발췌에서 위치 인용.

[^threshold]: 훈련 세트 크기 문턱(Config C 보상 Q1→Q4 0.344→0.325 하락, Config A·B 상승, 전환은 대략 60~150개 예제 사이)은 He et al., §5.3·Table 6 발췌 기준의 의역. 영어 verbatim 따옴표는 쓰지 않음.

[^filter]: 형식 특이적 노이즈(긴 assistant 응답이 메모리 항목의 약 50%를 차지하나 유용한 사실 없음) 필터링만으로 훈련 F1이 22% 개선(0.159→0.194)됐다는 발견은 He et al., §5.1 발췌에서 위치 인용.

[^f1reward]: GRPO를 단일 GPU 소그룹(G=4)에서 쓸 때 binary exact-match 보상은 그룹 내 분산이 0이 되어 무기울기 문제를 낳고, 연속값 F1 보상으로 전환해 해결했다는 서술은 He et al., §5.2 발췌 기준의 의역.

[^judge]: LLM-as-judge(Claude 3 Haiku, 1–5점) 대조에서 네 설정 평균이 3.22–3.39로 밀집하고 judge 순위가 F1과 다르지 않았다는 결과는 He et al., §4.3 발췌에서 위치 인용.

[^diff]: "Memory-R1 trains both a Memory Manager (for CRUD operations) and an Answer Agent... Our work focuses on the Answer Agent component... and studies how training data composition affects its learned skills. We use heuristic memory construction and focus our RL training on the answer generation policy, isolating the effect of curriculum composition from memory quality." — He et al.(arXiv:2605.23067). 원문 영어 verbatim, 제공 발췌 기준.

[^limits]: Limitations(§6) 세 문장 원문 영어 verbatim: "Single-GPU constraints... The smaller group size necessitated switching from exact-match to F1 reward and likely limits absolute performance." / "We use heuristic extraction rather than a trained Memory Manager... Prior work attributes roughly 7.5 F1 points to RL-trained memory management." / "All experiments use Qwen-2.5-7B-Instruct. Replication across Llama-family and Mistral-family backbones would test whether the specialization pattern we report is model-specific." — He et al.(arXiv:2605.23067). 제공 발췌 기준.
