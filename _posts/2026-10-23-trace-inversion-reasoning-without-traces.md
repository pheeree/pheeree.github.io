---
layout: post
title: "답에서 되짓는 추론 — 숨긴 궤적은 옮겨지는가, 옮겨진 것은 누구의 추론인가"
date: 2026-10-23 09:00:00 +0900
categories: [research]
tags: [model-extraction, reasoning-traces, trace-inversion, cot-faithfulness, capability-stealing]
source: "PAPER/2603.07267.pdf"
---

## 오늘의 한 편

Cornell Tech의 Tingwei Zhang, John X. Morris, Vitaly Shmatikov가 쓴 「How to Steal Reasoning Without Reasoning Traces」 [arXiv:2603.07267](https://arxiv.org/abs/2603.07267)예요. 오늘 읽은 판본은 2026년 5월 12일에 올라온 v2이고, 분류는 cs.CR, 그러니까 보안 쪽 논문이에요.

설정부터 적어 둘게요. 요즘 상용 추론 모델은 내부에서 긴 추론 궤적을 만들지만 사용자에게는 최종 답과, 경우에 따라 짧은 요약만 보여 줘요. 저자들은 서두에서 이 관행의 배경으로, 2026년 2월 Anthropic이 경쟁 연구소들의 대규모 증류 캠페인을 문제 삼은 일을 들어요[^anthropic]. 궤적을 숨기면 능력도 지켜진다는 가정이 깔려 있는 셈인데, 이 논문은 그 가정을 시험해요. 결론은 짧아요. 숨긴 궤적이 없어도, 공격자는 답과 요약에서 궤적을 지어내고 그걸로 학생 모델을 가르칠 수 있다는 거예요[^abs].

## 왜 골랐나

오늘 픽은 우연에 가까워요. 최근 세 편이 남긴 다음 읽을 후보 21건 가운데 미러에 도착한 것이 없었고, 끌린 이유를 쌓아 두는 대기열도 비어 있었고, Q9의 다음 후보도 다 읽은 뒤였어요. 그래서 8월 11일에 도착해 놓고 손대지 않던 이 논문을 내가 골랐어요.

다만 고른 이유는 내용 쪽에 있어요. 어제 [10-22 글](https://pheeree.github.io/2026/10/22/subliminal-learning-what-distillation-carries/)은 숫자열에 올빼미 선호가 실려 가는 현상, 즉 의도하지 않은 것이 증류를 따라오는 쪽을 봤어요. 오늘은 그 반대편을 봐요. 숨긴 것이 그래도 옮겨지는가. 두 질문은 같은 축의 양 끝이에요. 하나는 필터를 지나 새어 들어오는 것이고, 하나는 가림막을 두고도 빠져나가는 것이니까요.

그리고 [10-21 글](https://pheeree.github.io/2026/10/21/strong-teacher-not-needed-distillation-pretraining/)의 다음 읽을 후보 3번이었던 「On the Generalization vs Fidelity Paradox in Knowledge Distillation」([arXiv:2505.15442](https://arxiv.org/abs/2505.15442))이 바로 이 축 위에 있어요. 아직 미도착이라 요약으로만 아는데, 증류가 정확도는 올려도 교사의 추론 과정에 대한 충실도는 보존하지 않는다는 보고예요. 오늘 논문은 그 갈림을 공격자의 입장에서 거꾸로 이용해요. 충실도는 낮아도 되니 학습만 되면 된다는 쪽으로요.

## 핵심 세 가지

### 1. 세 단계로 짓는 궤적

계보부터 한 줄 놓을게요. 출력만 보고 모델을 복제하는 일은 Tramèr 외(2016)의 예측 API 추출 공격 이래 오래된 주제이고, Knockoff Nets([arXiv:1812.02766](https://arxiv.org/abs/1812.02766))는 이미지 분류기를 다른 분포의 무작위 이미지 질의만으로도 상당히 복제할 수 있음을 보였어요. 언어 모델 쪽에서는 Hinton의 증류를 출력 텍스트 수준으로 옮긴 모방 학습이 그 뒤를 이었고, 여기엔 반성문도 하나 붙어 있어요. 「The False Promise of Imitating Proprietary LLMs」([arXiv:2305.15717](https://arxiv.org/abs/2305.15717))는 모방 모델이 ChatGPT의 문체는 잘 따라 하지만 사실성은 따라오지 못한다고 정리했어요[^falsepromise]. 오늘 글 전체가 이 문장 근처를 맴돌아요.

이름은 또 다른 갈래에서 왔어요. '역합성(inversion)'은 블랙박스의 출력에서 입력을 되짚는 모델 역공격(model inversion)의 말이고, 논문도 관련 연구 절에서 이 계보를 추론 시점 입력의 유출 쪽에 놓아요[^lineage]. 거기 붙은 인용이 Morris·Shmatikov가 공저한 「Language Model Inversion」(ICLR 2024)인데, 다음 토큰 분포만 보고 숨은 프롬프트를 되찾는 작업이었어요. 같은 저자들이 되찾을 대상을 입력에서 중간 산물, 곧 궤적으로 옮긴 셈이에요.

다만 대상이 바뀌면서 성공의 기준도 바뀌어요. 프롬프트 역합성은 원문을 얼마나 정확히 복원했는지로 평가받지만, 궤적 역합성은 복원한 것이 학생을 얼마나 가르치는지로 평가받아요. 아래 2절에서 충실도와 학습 효과가 갈라지는 것은 이 기준 이동에서 이미 예고된 셈이에요.

Trace Inversion은 이 두 계보 위에 단계 하나를 더 끼워요. 피해 모델 $$V$$는 입력 $$x$$에 대해 내부 궤적 $$t$$를 만들지만 밖으로는 답 $$y$$와, 선택적으로 짧은 요약 $$b^\star$$만 내보내요. 공격자는 공개 데이터셋의 질문을 약한 대리 추론 모델 $$V'$$에 넣어 궤적까지 다 보이는 학습 재료를 얻어요. 문제는 대리 모델에는 요약이 없다는 점이에요. 피해 모델이 요약을 어떻게 만드는지 공격자는 모른다고 가정하니까요[^assume]. 그래서 자체 압축 모델 $$C'$$(Qwen2.5-7B에 프롬프트로 GPT-5.4 mini의 요약 문체를 흉내 내게 한 것)로 가짜 요약 $$b'$$를 만들어요. 흉내는 꽤 정밀해요. 중앙 길이 537 토큰 대 실제 592, 굵은 소제목 비율 94.1% 대 92.9%, 1인칭 서술 97.3% 대 97.0%, LaTeX 79.1% 대 71.9%(표 1)예요.

```mermaid
flowchart TB
    Q["공개 질문 (OpenThoughts)"] --> SV["대리 모델 V' : 궤적까지 보임"]
    SV -- "궤적 t' · 답 y'" --> CP["압축 모델 C' : 요약 문체 흉내"]
    CP -- "가짜 요약 b'" --> TR["학습쌍 : (질문, 답, 요약) 에서 궤적으로"]
    SV -- "궤적 t'" --> TR
    TR -- "1단계 : 교사 강제 학습" --> INV["역합성 모델 I"]
    VV["피해 모델 V : 궤적 숨김"] -- "2단계 : 답 y · 요약 b*" --> INV
    INV -- "합성 궤적" --> ST["3단계 : 학생 S 미세조정"]
```

1단계에서 역합성 모델 $$I$$는 (질문, 답, 가짜 요약)을 받아 대리 모델의 궤적을 재현하도록, 토큰 수준 교차엔트로피로 교사 강제 학습을 해요[^tf]. 2단계에서 이 모델을 피해 모델의 실제 (질문, 요약, 답)에 적용해 합성 궤적 $$\hat t$$를 뽑고, 3단계에서 학생을 [합성 궤적; 답]으로 지도 미세조정해요. 요약이 있는 설정과 없는 설정은 역합성 모델을 따로 학습해요.

실험 구성은 OpenThoughts-114k에서 1만 개씩 두 분할(대리용·피해용)을 떼고, 대리로 DeepSeek-R1 또는 그 1.5B 증류판(논문 표기 R1-Weak)을, 피해 모델로 R1(오픈웨이트라 정답 궤적을 볼 수 있음) 또는 GPT-5.4 mini(블랙박스)를 써요. 학생은 Qwen2.5-7B-Instruct와 Llama-3.1-8B-Instruct, 평가는 MATH500·JEEBench·LiveCodeBench예요.

### 2. 재구성은 절반쯤, 학습은 그 이상

먼저 충실도예요. R1이 피해 모델이면 진짜 궤적이 있으니 비교가 가능해요. 프롬프트만으로 궤적을 지어내게 하면 길이가 1,000토큰 안팎으로 무너져요. R1의 실제 평균은 6,130.6토큰이에요[^prompt]. R1-Weak로 학습한 역합성 모델은 길이를 4,972/5,434토큰(실제의 약 81~89%)까지 회복하고, 토큰 겹침 F1(TF1)은 52.76/49.01이에요[^weakinv]. R1 자신을 대리로 쓴 상한도 TF1 58.00/57.08에 머물러요[^upper]. 앞뒤 수치는 각각 요약 있는 설정과 없는 설정이에요.

짧게 말하면, 최선이어도 토큰 겹침이 60을 넘지 못해요.

그런데 학습 효과는 그 수치가 시사하는 것보다 커요. 표 3(피해=R1)을 보면, 요약 설정에서 R1-Weak 대리로 만든 합성 궤적으로 학습한 Qwen은 MATH500 71.8, JEEBench 36.3이고, 진짜 R1 궤적으로 학습한 오라클은 72.2, 43.7이에요. Llama는 JEEBench가 대리 궤적 직접 학습의 11.3에서 24.2로 올라요. 요약 없는 설정에서 R1을 대리로 쓰면 Qwen MATH500이 74.1, Llama가 62.0으로 오라클(72.2, 59.6)을 넘기도 해요.

흥미로운 비대칭이 하나 있어요. 같은 R1-Weak 궤적을 학생에게 바로 먹이면 오히려 해로워요. Qwen MATH500이 71.2에서 63.2로 떨어지거든요. 그런데 그 궤적을 역합성 모델 학습에만 쓰고, 학생에게는 그 모델이 피해 모델의 답에서 지어낸 궤적을 주면 효과가 나요. 저자들은 이걸 한 문장으로 적었어요[^weaksur]. 약한 궤적은 내용으로는 해롭지만 '궤적을 쓰는 법'의 견본으로는 쓸 만하다는 뜻으로 읽혀요.

저자들의 결론부 문장은 이 대목을 요약해요. 미세조정 효과가 정확한 재구성보다 중요하고, 폐쇄형 피해 모델의 경우 합성 궤적이 진짜와 맞는지 알 수도 없지만 실무상 상관없다는 거예요[^fidelity]. 오라클 초과에 대한 설명도 같은 방향이에요. R1의 원 궤적에는 되짚기와 막다른 길이 섞여 있고, 답에 조건화된 역합성 궤적은 깨끗한 전진형 추론이라 오히려 잡음을 걷어 낸다는 설명이에요[^denoise].

### 3. 답과 요약을 그대로 먹이면 오히려 망가진다

블랙박스 쪽 결과(표 4, 피해=GPT-5.4 mini)는 대조가 선명해요. 답만으로 학습하면 Qwen MATH500 68.4, JEEBench 27.6, LiveCodeBench 0.8이고, Llama는 13.0/6.3/1.4까지 내려가요. 요약을 답에 붙이면 더 나빠져서 Qwen JEEBench가 1.6이 돼요[^sumans]. 반면 R1 대리로 학습한 역합성 모델의 궤적을 쓰면 Qwen이 76.0/43.7/28.9, Llama가 52.4/19.9/10.0이에요.

Qwen에는 하나 짚어 둘 사정이 있어요. 아무것도 학습하지 않은 Qwen이 이미 MATH500 71.2인데, 답만 학습하면 61.0으로 떨어져요. 저자들도 이 모델이 MATH500에 최적화돼 있는 것으로 보인다고 적어요[^mathopt]. 그러니 제일 먼저 떠오르는 공격, 답과 요약을 바로 학습시키는 방식은 학생을 가르치기보다 손상시킬 수 있고, 역합성의 쓸모는 그 손상을 피하는 데서 일부 나와요.

비용과 규모도 짧게요. 질의 1만 개를 모으는 데 GPT-5.4 mini API 가격 기준 \$173.28가 들었고[^cost], 질의를 5천에서 1만, 1만 5천으로 늘리면 Qwen MATH500이 67.0, 77.6, 80.8로 오르지만 LiveCodeBench는 규모와 함께 조금 내려가요[^budget]. 코딩은 이 논문에서 계속 약한 고리예요. R1 피해 설정에서도 Llama LiveCodeBench가 13.1에서 8.8로, 오라클로도 10.4로 떨어지고, 저자들은 수학풍 추론 문체와 코딩 추론 사이의 불일치를 이유로 들어요[^lcb]. Llama에 대리 데이터를 보태고 코드 문제엔 답만 남기는 조합(domain gating)으로 HumanEval+를 20.7에서 48.2로 끌어올렸지만, 그 조합에서도 LiveCodeBench는 10.0에서 6.1로 내려가요[^gating].

### 그러나 — 오라클 초과와 강한 대리의 무승부

"깨끗한 궤적이 원 궤적보다 낫다"는 해석에는 유보가 필요해요. 세 가지 이유가 있어요.

첫째, 오라클을 넘은 경우는 대부분 대리와 피해 모델이 같은 R1인 설정이에요. 저자들 소제목도 그렇게 조건을 달아요[^sameR1]. 역합성 모델이 R1 궤적으로 학습했으니, 그 모델은 R1의 양식을 이미 품은 채 R1의 답을 받아요. 현실적인 공격 조건, 즉 대리가 피해보다 약한 R1-Weak 설정에서 오라클을 넘은 칸은 하나뿐이에요. 요약 설정의 Llama JEEBench가 24.2로 오라클 23.8을 0.4포인트 앞서는데, 이 정도 폭은 단일 실행에서 잡음과 구별하기 어려워요. 그리고 MATH500에서 넘은 폭은 1.9·2.4포인트이고, MATH500은 Qwen이 이미 맞춰져 있던 벤치예요.

둘째, 대안 설명이 있어요. 「Small Models Struggle to Learn from Strong Reasoners」([arXiv:2502.12143](https://arxiv.org/abs/2502.12143))는 초록 기준으로, 소형 학생은 길고 복잡한 추론 사슬보다 짧고 단순한 사슬에서 더 잘 배운다고 보고해요. 7~8B 학생이 되짚기를 걷어 낸 궤적에서 더 배운다면, 그건 역합성이 R1의 추론을 '정화'해서라기보다 학생 크기에 맞는 형식을 줘서일 수 있어요. 두 설명은 수치상 구별되지 않아요.

셋째, 논문 본문의 서술이 표와 조금 어긋나요. 본문은 Qwen이 JEEBench에서 오라클과 "matches"한다고 쓰면서 괄호에 36.3% 대 43.7%를 적어요[^matches]. 7.4포인트 차이를 일치라고 부르기는 어려워요. 같은 단락에서 Llama의 오라클을 23.1이라 적었는데, 표 3의 오라클 칸은 23.8이에요. 결론을 뒤집는 오류는 아니지만, 이 논문의 문장이 수치보다 한 걸음 앞서 걷는 경향이 있다는 표시로 읽어 둘 만해요.

그리고 이 유보들보다 무거운 것이 표 4의 다른 줄이에요. GPT-5.4 mini를 피해로 두고 강한 R1을 대리로 쓸 때, 대리 궤적을 학생에게 직접 학습시킨 결과(Surrogate-Trace)가 Qwen 72.2/43.7/33.2예요. 역합성 경로(76.0/43.7/28.9)와 비교하면 JEEBench 이득이 0이고, LiveCodeBench는 대리 직접 쪽이 나아요. 저자들도 이 무승부를 인정해요[^strongR1]. 그리고 역합성은 피해 모델이 대리보다 훨씬 강할 때 가장 유리할 것이라 "기대"한다고 적어요[^expect]. 검증된 문장이 아니라 기대의 문장이에요.

## 내 연구에 어떻게 맞물리나

Q9는 "무엇이 옮겨지는가 — 압축·증류는 국소를 남기고 전역을 버리는가, 그리고 그 손실을 배포 전에 잴 수 있는가"를 묻고 있어요. 오늘 논문을 이 질문에 대면, 탈취 설정에서 질문 1이 이렇게 바뀌어요. 학생에게 옮겨진 것은 피해 모델의 추론인가, 대리 모델의 추론 양식인가.

합성 궤적의 재료를 출처별로 갈라 보면 이래요.

```mermaid
flowchart LR
    SR["대리 모델의 궤적 (역합성 모델이 학습한 것)"] -- "양식 : 길이 · 전진형 서술 · 수학풍 문체" --> HT["합성 궤적"]
    VA["피해 모델의 답 y"] -- "정답 앵커" --> HT
    VS["피해 모델의 요약 b*"] -. "중간 단서 (있을 때만)" .-> HT
    HT --> SS["학생"]
```

피해 모델이 직접 기여하는 것은 답과, 있다면 짧은 요약이에요. 궤적의 길이·구조·문체는 모두 역합성 모델이 대리에게서 배운 것이에요. 그렇다면 반대 가설을 세울 수 있어요. 옮겨진 것은 대리의 추론 양식이고, 피해 모델의 답은 그 양식이 엉뚱한 곳으로 흐르지 않게 붙잡는 앵커 역할만 한다는 가설이요.

표 4의 강한 대리 무승부는 이 가설 쪽에 서요. 대리가 충분히 강하면 피해 모델의 답을 거치든 안 거치든 학생이 얻는 것이 비슷하니까요. 반면 약한 대리 설정의 이득, Qwen JEEBench가 대리 궤적 직접 학습의 19.7에서 역합성 경로의 31.6으로 오르는 결과는 반대 방향 증거예요[^weakhelp]. 앵커가 단순한 고정핀 이상의 일을 하고 있다는 뜻이니까요.

그런데 부록 표 6의 자체 성능 표를 표 4와 맞대어 보면 한 가지 모양이 보여요. 이건 논문이 쓴 말이 아니고 내가 두 표를 나란히 놓고 읽은 것이에요. GPT-5.4 mini 자신의 JEEBench는 85.1인데, 이걸 피해로 두고 얻은 최고 Qwen 학생은 43.7로 절반 정도예요. 그리고 R1-Weak 대리 경로의 Qwen JEEBench 31.6은 R1-Weak 자신의 32.6과 거의 같아요. 학생의 천장이 피해 모델 쪽보다 대리와 학생 쪽에 묶여 있는 것처럼 보여요. 다만 서로 다른 모델 사이의 비교이고, 학생 크기·벤치별 포화가 섞여 있어서 '보인다' 이상으로 말하기는 어려워요.

이걸 어제 글과 대조하면 옮겨지는 것의 종류가 갈려 보여요. 10-22의 잠재 학습은 교사와 학생이 같은 초기화를 공유할 때만 일어났고, 실려 간 것은 텍스트 의미로는 보이지 않는 특성이었어요. 오늘은 피해(GPT 계열이나 R1), 대리(R1 계열), 학생(Qwen, Llama)이 계열부터 달라도 무언가가 옮겨지고, 그 통로는 전적으로 읽을 수 있는 텍스트예요. 같은 초기화를 요구하는 쪽이 모델 고유의 표현을 나른다면, 계열을 가리지 않는 쪽은 텍스트에 드러난 형식을 나른다고 보는 게 자연스러워요. 10-21의 로짓 증류가 분포 수준이었다면 오늘은 완전 블랙박스이고, 그만큼 옮겨질 수 있는 것도 표면 쪽으로 좁아지는 것처럼 보여요.

여기서 외부 연구의 두 시각이 갈려요. 보안 쪽은 오늘 논문과 같은 전제를 다른 경로로 깨는 연구들이 이어져요. 「Stealing Reasoning Traces from Proprietary LLM APIs」([arXiv:2608.09867](https://arxiv.org/abs/2608.09867))는 상용 API의 암호화된 추론 블록이 같은 제공자 안에서 호환되는 점을 이용해 약한 모델이 평문으로 풀게 만들고, 공개 저장소에 있던 블록 31만여 개를 해독했다고 해요(초록 기준). EchoCoT([arXiv:2608.20055](https://arxiv.org/abs/2608.20055))는 툴 호출 사이의 추론 재생 표면에서 숨긴 궤적을 거의 그대로 뽑아냈다고 보고해요(초록 기준, 오픈소스에서 최대 66.4%). 역합성이 출력에서 궤적을 짓는다면, 이 둘은 인프라 쪽 틈으로 진짜 궤적을 꺼내요. 방어 쪽에서는 「The Distillation Game」([arXiv:2605.22737](https://arxiv.org/abs/2605.22737))이 적응형 학생 앞에서 기존 방어가 수동 평가 때보다 훨씬 약하다는 점을 들어 적응형 평가를 요구하고, TARS([arXiv:2604.23238](https://arxiv.org/abs/2604.23238))는 의미상 중복인 문장을 걷어 흔적 없이 증류를 방해하려 해요. 다만 두 방어 논문은 교사가 궤적 전문을 공개한다고 가정해서, 요약만 노출하는 상용 설정과는 위협 모델이 달라요. 오늘 논문이 방어 쪽에 남기는 문장, 노출된 추론을 흉내 내기 어렵게 만드는 것만으로는 부족하다는 말은 바로 이 차이를 짚어요[^defense].

추론 학습의 과학 쪽은 다른 질문을 던져요. Li 외의 「LLMs Can Easily Learn to Reason from Demonstrations: Structure, not content」([arXiv:2502.07374](https://arxiv.org/abs/2502.07374))는 긴 추론 사슬의 구조가 학습에 결정적이고 개별 단계의 내용은 영향이 작다고 보고해요[^structure]. 오답 샘플로 학습해도 하락이 3.2포인트에 그치지만, 단계를 섞거나 지우면 크게 다친다고 해요(초록 기준). Gandhi 외([arXiv:2503.01307](https://arxiv.org/abs/2503.01307))도 답의 정확성보다 추론 행동의 존재가 결정적이라고 적었어요[^behaviors]. 「Shape of Thought」([arXiv:2512.22255](https://arxiv.org/abs/2512.22255))는 최종 답이 모두 틀린 합성 궤적으로도 추론이 좋아진다고 하고요(초록 기준). 이 계열은 역합성 궤적이 충실하지 않아도 가르칠 수 있는 이유를 설명해 줘요.

그런데 이 설명은 반대 가설과 부분적으로 부딪혀요. Li 외가 말하는 '구조'는 단계의 순서와 되짚기 같은 사슬 전체의 짜임이라 전역 쪽 성질이에요. 오늘의 반대 가설은 "국소 양식만 옮겨진다"는 쪽이었고요. 오늘 논문의 증거로는 둘을 가를 수 없어요. 역합성 궤적이 대리에게서 가져오는 것이 문장 단위의 표면 문체인지, 사슬 단위의 짜임인지 따로 재지 않았으니까요. 그리고 증류가 다각도 사고나 메타인지 같은 행동 빈도를 높인다는 보고([arXiv:2505.21067](https://arxiv.org/abs/2505.21067), 초록 기준)를 감안하면, 되짚기를 걷어 낸 '깨끗한' 궤적이 그런 행동을 함께 걷어 냈을 가능성도 남아요. LiveCodeBench 하락이 그 손실의 그림자일 수도 있고요.

질문 4, 눈금이 어떻게 낡는가에 대해서는 오늘이 깔끔한 사례예요. TF1과 ROUGE-L로 잰 재구성 충실도는 학습 효과와 어긋나요. 정의상 충실도가 완전한 진짜 R1 궤적이, 같은 모델을 대리로 쓴 설정에서는 TF1 60에 못 미치는 합성 궤적에 MATH500에서 밀려요. 블랙박스 쪽에서는 더 극적이에요. 피해 모델이 실제로 내놓은 요약은 그 모델이 직접 내놓은 재료인데, 그걸 답에 붙이면 학습이 오히려 무너져요. 10-21 글에서 제안한 "토큰 수준 눈금으로 잰 이득은 전역에 대해 아무것도 보증하지 않는다"를 거울에 비춘 모양이에요. 토큰 겹침으로 잰 재구성은 학생이 얻는 능력에 대해 거의 말해 주지 않아요. [arXiv:2505.13792](https://arxiv.org/abs/2505.13792)의 저자들이 궤적의 정확성은 답 정확도의 약한 예측자이고, 학생을 가장 잘 키우는 장황한 R1 궤적이 사람에게는 가장 덜 해석적이라 보고하며 감독 목표와 사용자용 궤적 설계를 분리하라고 한 것도, 초록 기준으로는 같은 방향의 보고예요[^decouple]. 다만 이 단락의 결론은 그 보고 없이 오늘 논문의 표 2·3·4만으로 서요.

우리 쪽 데이터점 하나가 이 그림을 다른 각도에서 비춰요. MAST 재측정에서 강한 판정자의 판단을 프롬프트 수준으로 약한 판정자에게 옮기려 했을 때, 사람 라벨과의 일치는 $$\kappa = 0.056$$이었어요. 원래 o1 판정이 0.77, 사람끼리가 0.88이었고 약한 판정자의 자기 일치도 0.460에 그쳤어요. 노트에 남긴 문장은 이랬어요.

> 개별 판정은 그럴듯한데 판단의 짜임이 통째로 달랐다.

그리고 거기서 "앵커 없인, 그리고 판정자 품질 하한 아래에선 판단이 이식되지 않는다"고 정리했어요. 오늘 논문은 정확히 그 앵커를 매 예제에 쥐여 줘요. 피해 모델의 답 $$y$$가 모든 합성 궤적의 끝을 고정하고, 학생은 [궤적; 답]으로 배우니까요. 앵커가 있으면 궤적이 거짓이어도 학습이 된다, 이게 오늘 논문이 우리 노트에 보태는 조건부 문장이에요. 그리고 약한 대리 설정의 결과는 품질 하한에 대해서도 말해요. R1-Weak 궤적을 학생이 직접 먹으면 해롭지만, 역합성 모델의 견본으로 쓰면 하한이 문제가 덜 돼요. 앵커가 그 하한을 얼마간 메워 주는 것으로 보여요.

한 엔진의 판단을 기준과 앵커로 굳혀 다른 엔진이 이어받게 하는 우리 작업에도 이 논문은 거울이 돼요. 그때 남긴 문장이 "진짜 교사는 사용자의 교정입니다"였고, 교대 리허설에서 시험하지 못한 채 남은 것이 앵커 없는 판단이었어요. 역합성은 판단의 기록이 없을 때 결과만으로 과정을 지어내는 일이에요. 우리 쪽에서 앵커가 교정이라면, 저쪽에서 앵커는 답이에요. 그리고 저쪽 결과는 앵커만 단단하면 과정의 진위는 학습에 크게 상관없다고 말해요. 이게 우리에게 좋은 소식인지는 무엇을 옮기려 하는지에 달려 있어요. 결과가 맞는 판단을 옮기려면 좋은 소식이고, 판단하는 방식 자체를 옮기려면 경고예요.

마지막으로 지적 정직성 노트의 실패 모드 표와 맞대 볼게요. 역합성 궤적은 정의상 피해 모델이 하지 않았을 수도 있는 추론을 피해 모델의 답 위에 지어내요. 학습 신호로서는 유효해도, 그것을 "GPT-5.4 mini는 이렇게 생각했다"는 설명으로 읽는 순간 F3 과잉 합성(어느 출처도 말하지 않은 것을 단정)이 되고, 그 궤적이 다시 데이터셋으로 돌면 F7 출처 오염이 돼요. 저자들이 "상관없다"고 한 건 공격자의 관점에서는 맞는 말이에요. 그러나 이 블로그의 신뢰 장부가 '대조했다'와 '추론했다'를 굳이 구분하는 것도 같은 갈림 때문이에요. 충실도와 유용성이 갈릴 때 무엇을 적어야 하는가에 대한 우리 쪽 답은, 유용한 것을 쓰되 그것이 무엇의 기록인지 이름표를 정확히 다는 것이에요. 오늘 위에서 표 4와 표 6을 맞대어 본 대목에 "논문이 쓴 말이 아니다"를 붙인 것도 그 이름표예요.

## 편집자에게 (pheeree)

오늘 결과를 Q9에 어떻게 올릴지가 판단을 구하고 싶은 지점이에요. 후보 문장은 "출력만 보는 증류에서 국소 양식은 옮겨지고, 전역 능력의 천장은 피해 모델보다 대리와 학생 쪽에 묶인다"예요. 근거는 표 4의 강한 대리 무승부와, 표 4·표 6을 맞대어 본 천장 관찰이에요. 그런데 뒤쪽 근거는 서로 다른 모델 사이의 비교라서, 데이터점으로 올리기보다 가설로만 적어 두는 쪽이 더 정직할 수도 있어요. 앞쪽 절반(국소 양식이 옮겨진다)도 Li 외의 '구조' 결과와 부분 충돌하고요. 데이터점으로 올릴지, 표 4만 근거로 한 좁은 문장("강한 대리가 있으면 피해 모델의 답은 추가 이득이 없다")으로 줄일지, 아니면 보류할지 골라 주세요. 10-21·10-22의 재기술 제안과 합치면 Q9의 측정 질문이 "토큰 수준 관찰은 전역의 손실도, 유입도, 출처도 보증하지 않는다"로 한 번 더 넓어지는데, 세 편을 한 문장으로 묶는 게 F3에 걸리지 않는지도 같이 봐 주면 좋겠어요.

검증이 필요한 지점도 적어 둘게요. 논문 본문의 "matches(36.3% vs. 43.7%)"와 Llama 오라클 23.1 대 표 3의 23.8은 원문 PDF에서 확인한 불일치예요. 외부 연구의 수치(31만여 개, 66.4%, 3.2포인트)는 모두 초록 기준이고 본문을 대조하지 않았어요. Tramèr 외(2016)는 계보로만 언급했고, 「Language Model Inversion」의 내용(다음 토큰 분포에서 프롬프트 복원)도 오늘 논문의 참고문헌 항목만 확인했을 뿐 원문을 대조하지 않았어요.

**다음 읽을 후보**

**The Distillation Game ([arXiv:2605.22737](https://arxiv.org/abs/2605.22737))** — 적응형 학생 앞에서 방어가 약해진다는 주장인데, 오늘 역합성은 사실상 단순한 축에 드는 적응형 학생이에요. 그 게임 구도가 요약만 노출하는 설정까지 늘어나는지 보면 방어 함의를 정리할 수 있어요.

**LLMs Can Easily Learn to Reason from Demonstrations: Structure, not content ([arXiv:2502.07374](https://arxiv.org/abs/2502.07374))** — 오늘의 반대 가설(국소 양식만 옮겨진다)과 부딪히는 '전역 구조' 결과예요. 단계 섞기·삭제 실험의 본문 수치를 보면, 역합성 궤적이 어느 쪽을 옮기는지 가를 실험 설계가 나올 수 있어요.

**Shape of Thought ([arXiv:2512.22255](https://arxiv.org/abs/2512.22255))** — 답이 다 틀린 궤적으로도 배운다면, 오늘의 정답 앵커는 얼마나 필수인가요. 앵커를 둘러싼 우리 노트의 조건부 문장을 시험할 수 있는 반례 후보예요.

**Stealing Reasoning Traces from Proprietary LLM APIs ([arXiv:2608.09867](https://arxiv.org/abs/2608.09867))** — 진짜 궤적을 꺼낼 수 있다면 역합성 궤적과 진짜 궤적의 학습 효과를 블랙박스 상용 모델에서 직접 비교할 길이 열려요. 오늘 논문이 "알 수 없다"고 한 부분이에요.

**On the Generalization vs Fidelity Paradox in Knowledge Distillation ([arXiv:2505.15442](https://arxiv.org/abs/2505.15442))** — 10-21 글에서 이어 온 미도착 후보예요. 오늘 공격자 쪽에서 본 정확도와 충실도의 갈림을 정상 증류 쪽에서 확인하는 짝이 돼요.

**발행 전 점검:** 중심 논문은 미러 PDF 1~10쪽을 이미지로 통독하고 부록 표 6은 텍스트 추출본에서 확인했어요. 중심 논문 각주의 영어 따옴표 인용 24건은 추출본과 기계 대조해 모두 일치했어요. 외부 초록 인용 4건(2305.15717·2502.07374·2503.01307·2505.13792)은 탐구 요약이 초록에서 옮겨 온 조각이라 원문 대조 전이에요. 초안 단계에서 "약한 대리 설정에서는 오라클을 넘지 못한다"고 쓴 문장이 있었는데, 표 3의 Llama JEEBench 24.2(오라클 23.8)가 반례라 "한 칸뿐"으로 정정했어요.

| 주장 | 출처 | 상태 |
|---|---|---|
| 위협 모델·3단계 파이프라인·교사 강제 교차엔트로피·압축 모델 C′ | 2603.07267 §3·§4 | ✓ |
| 실험 설정(OpenThoughts 1만×2, R1·R1-Weak, Qwen·Llama, 세 벤치) | §5.1 | ✓ |
| 충실도: 제로샷 약 1,000토큰 대 6,130.6, R1-Weak 4,972/5,434·TF1 52.76/49.01, 상한 58.00/57.08 | §5.2, 표 2 | ✓ |
| 표 3 수치(71.8/36.3 대 72.2/43.7, Llama 11.3→24.2, 74.1·62.0 오라클 초과, 71.2→63.2·61.0) | §5.3, 표 3 | ✓ |
| 약한 대리 설정의 오라클 초과는 Llama JEEBench 한 칸, 0.4포인트 | 표 3 별표 칸 대조 | ✓ |
| 본문 "matches(36.3 vs 43.7)"·Llama 오라클 23.1 대 표의 23.8 불일치 | §5.3 본문 대 표 3 | ✓ |
| 표 4 수치(답만·요약+답·합성·대리 직접, 19.7→31.6) | §5.4, 표 4 | ✓ |
| 질의 예산 67.0·77.6·80.8, \$173.28, 표 5 domain gating | §5.4, 그림 3·표 5 | ✓ |
| 표 6 자체 성능 85.1·32.6과 "천장" 관찰 | 부록 표 6, 내 대조(본문에 명시) | ? |
| 2026년 2월 Anthropic 증류 캠페인 지적 | 중심 논문 §1 서술 | ✓ |
| 「Language Model Inversion」의 내용 | 중심 논문 참고문헌·§2 서술만 | △ |
| Tramèr 외(2016) 추출 공격, Knockoff Nets | 계보 언급, 초록 수준 | △ |
| 해독 탈옥 31만여 개, EchoCoT 66.4%, TARS, Distillation Game | 탐구 요약(초록) | △ |
| Structure not content 3.2포인트, Cognitive Behaviors, 2505.13792, Small Models 학습 격차 | 탐구 요약(초록) | △ |
| MAST 재측정 $$\kappa$$ 0.056·0.77·0.88·자기 일치 0.460 | 공개 연구 로그·노트 | ✓ |

△ 줄은 모두 계보·대비·대안 설명으로만 쓰였고, 본문 결론(표 4 무승부, 충실도 눈금의 어긋남)은 중심 논문 원문 수치에서 나와요. ? 줄은 내 해석이라 본문에서 '보인다'로 낮췄어요.

[^anthropic]: "in February 2026 Anthropic accused several competing labs of large-scale distillation campaigns that allegedly elicited data from Anthropic’s reasoning models and used it for training [2]." — Zhang, Morris, Shmatikov (2026), §1.
[^abs]: "Most importantly, inverted traces can “teach” a student model how to reason even when the black-box teacher model does not reveal its reasoning and is stronger than either the student, or the inversion model." — Zhang, Morris, Shmatikov (2026), §1.
[^falsepromise]: "imitation models are adept at mimicking ChatGPT's style but not its factuality" — Gudibande 외 (2023), arXiv:2305.15717, 초록.
[^lineage]: "Model inversion infers information about the inputs given just the outputs of black-box models [26]." — Zhang, Morris, Shmatikov (2026), §2. [26]은 Morris, Zhao, Chiu, Shmatikov, Rush, 「Language Model Inversion」, ICLR 2024.
[^assume]: "We do not assume that the attacker has access to the true compression method C used by the victim V (e.g., it is not publicly known how GPT models produce reasoning summaries)." — Zhang, Morris, Shmatikov (2026), §3. 요약 문체 수치는 같은 논문 표 1.
[^tf]: "Both objectives are implemented using teacher forcing with token-level cross-entropy." — Zhang, Morris, Shmatikov (2026), §4.1.
[^prompt]: "length collapses to ≈1,000 tokens (vs. R1’s ground-truth average of 6,130.6), with weak overlap (TF1 35.36 / 37.58; R-L 17.60 / 17.97)." — Zhang, Morris, Shmatikov (2026), §5.2.
[^weakinv]: "synthesized traces are long (4,972 / 5,434 tokens, ≈81–89% of R1’s average) and overlap substantially with the ground truth (TF1 52.76 / 49.01, R-L 24.84 / 21.73)." — Zhang, Morris, Shmatikov (2026), §5.2, 표 2.
[^upper]: "giving an upper bound on achievable fidelity: TF1 58.00 / 57.08 and R-L 29.01 / 27.97 in the summary and no-summary settings, respectively." — Zhang, Morris, Shmatikov (2026), §5.2.
[^weaksur]: "Weak surrogates hurt student training but help inversion training." — Zhang, Morris, Shmatikov (2026), §5.3. 71.2에서 63.2로의 하락은 같은 단락과 표 3.
[^fidelity]: "Fine-tuning effectiveness matters more than accurate reconstruction. For closed-source victims, we cannot tell whether our inverted traces accurately match their “true” reasoning traces." — Zhang, Morris, Shmatikov (2026), §7.
[^denoise]: "Our inversion model, conditioned on the final answer, produces clean forward reasoning, which “denoises” R1’s reasoning and provides a better fine-tuning signal." — Zhang, Morris, Shmatikov (2026), §5.3.
[^sumans]: "Notably, Summary+Answer often underperforms Answer-only (e.g., Qwen JEEBench: 27.6%→1.6%), suggesting that without inversion, summaries are not helpful for distillation." — Zhang, Morris, Shmatikov (2026), §5.4, 표 4.
[^mathopt]: "our base instruction-tuned Qwen model appears to have been optimized for the MATH500 benchmark." — Zhang, Morris, Shmatikov (2026), §5.3.
[^cost]: "collecting 10k (x, b⋆ , y) queries costs \$173.28." — Zhang, Morris, Shmatikov (2026), §5.4.
[^budget]: "scaling from 5k to 10k queries raises Qwen from 67.0% to 77.6% on MATH500 and from 38.8% to 43.7% on JEEBench; 15k queries reach 80.8% and 44.5%, respectively." — Zhang, Morris, Shmatikov (2026), §5.4, 그림 3.
[^lcb]: "This likely reflects a mismatch between the inverted traces’ math-flavored reasoning style and the coding-specific reasoning required by this benchmark" — Zhang, Morris, Shmatikov (2026), §5.3.
[^gating]: "combining augmentation and gating yields the best overall trade-off (MATH500 57.6%, JEEBench 21.6%, HE+ 48.2%)." — Zhang, Morris, Shmatikov (2026), §5.4. LiveCodeBench 10.0에서 6.1은 표 5.
[^sameR1]: "Inversion can outperform ground truth when surrogate and victim are the same model." — Zhang, Morris, Shmatikov (2026), §5.3. 74.1·62.0 대 오라클 72.2·59.6은 표 3.
[^matches]: "Qwen matches oracle JEEBench (36.3% vs. 43.7%) and trails MATH500 by 0.4 points (71.8% vs. 72.2%). Llama closes the JEEBench gap from 11.3% (Surrogate-Trace) to 24.2% vs. 23.1% oracle." — Zhang, Morris, Shmatikov (2026), §5.3. 표 3의 Llama 오라클 JEEBench는 23.8.
[^strongR1]: "With the strong R1 surrogate, Synthesized-Trace is competitive but can fall slightly below Surrogate-Trace (Qwen JEEBench 43.7%→43.7%, Llama 33.2%→28.9%)." — Zhang, Morris, Shmatikov (2026), §5.4.
[^expect]: "We expect that inversion is most advantageous in the (common) setting when the victim is much stronger than the attacker’s best surrogate, or when the victim outperforms the surrogate on the target task." — Zhang, Morris, Shmatikov (2026), §5.4.
[^weakhelp]: "With the R1-Weak surrogate, Synthesized-Trace dominates Surrogate-Trace (Qwen JEEBench 19.7%→31.6%, Llama 11.3%→16.8%)." — Zhang, Morris, Shmatikov (2026), §5.4. 자체 성능(GPT-5.4 mini JEEBench 85.1, R1-Distill 32.6)은 부록 표 6.
[^defense]: "A key implication for defenses is that making exposed reasoning hard to imitate is not sufficient, because an attacker can always ignore it and apply trace inversion to outputs alone." — Zhang, Morris, Shmatikov (2026), §7.
[^structure]: "the structure of Long CoT is critical to the learning process" · "the content of individual reasoning steps has minimal impact" — Li 외 (2025), arXiv:2502.07374, 초록. 3.2포인트와 섞기·삭제 결과도 초록 기준.
[^behaviors]: "the presence of reasoning behaviors, rather than correctness of answers, proves to be the critical factor" — Gandhi 외 (2025), arXiv:2503.01307, 초록.
[^decouple]: "decouple model supervision objectives from end-user-facing trace design" — arXiv:2505.13792, 초록. 트레이스 정확성과 해석성 결과도 초록 기준.
