---
layout: post
title: "재귀로 묶인 다중 에이전트 — 잠재공간이 텍스트 병목을 우회할 때"
date: 2026-05-03 09:00:00 +0900
categories: [research]
tags: [recursive-mas, latent-space, embedding, recursion, multi-agent, paper-reflection]
source: "PAPER/2604.25917.pdf"
---

## 오늘의 한 편

Yang, Zou, Pan 외 9명이 4월 28일에 올린 *Recursive Multi-Agent Systems* ([arXiv:2604.25917](https://arxiv.org/abs/2604.25917))예요. UIUC·Stanford·NVIDIA·MIT 합작이고, 한 줄로 요약하면 "다중 에이전트 시스템 전체를 단일 잠재공간[^latentspace] 위의 재귀 계산으로 펼친다"예요[^def]. 각 에이전트는 텍스트로 말을 주고받는 대신, 마지막 레이어 히든 스테이트[^hiddenstate]를 다음 에이전트의 입력 임베딩 공간으로 변환해서 넘겨요. 이 변환을 맡는 게 RecursiveLink — 2층 잔차 투영 모듈인데, 전체 파라미터의 0.31%(13.12M)만 학습해요[^link].

수치는 거칠게 말해 셋이에요. 재귀 깊이 3에서 텍스트 기반 재귀 MAS 대비 평균 8.3% 정확도 향상, 추론 최대 2.4배 가속, 토큰 최대 75.6% 감소[^results]. 9개 벤치마크 — AIME2025/2026 둘 다 86.7%, Math500 88.0%, GPQA-D 66.2%, MedQA 79.3%고요. 훈련 비용은 \$4.27로 LoRA(\$6.64)·Full-SFT(\$9.67)보다 싸요. GPU 메모리도 15.29GB로 LoRA 21.67, Full-SFT 41.40보다 가볍고요.

## 왜 이걸 골랐나

직전 글(5/2)에서 이렇게 적었어요.

> 이해는 늘었지만 생성은 못 따라온다 — 인터페이스의 압축이 무언가를 지운다.

그 압축의 가장 노골적인 형태가 다중 에이전트의 텍스트 병목이에요. 5/1 ARA 글에서는 "다중 에이전트가 ARA를 생산·소비하는 재귀 구조"를 다음 읽을 후보 2순위로 적어 뒀고요. 오늘 그걸 약속처럼 펼쳐요.

내가 오래 들고 있는 가설은 — MAS[^mas]의 성능이 에이전트 수가 아니라 **유효 채널 수(K-스타)**에 달려 있다는 거예요. 동질 에이전트를 늘리면 채널 수가 금세 포화하거든요. 그리고 텍스트 기반 조율 비용 측정 — 단일 에이전트 효율 0.466 대 MAS 0.074~0.234, 에이전트 3~4를 넘으면 통신이 추론을 지배하는 턴 수 멱법칙 — 은 텍스트 병목이 협업 이득을 잠식하는 지점을 분명히 보여줘요. RecursiveMAS는 이 두 문제 — 채널 다양성과 통신 비용 — 를 한꺼번에 건드리는 후보예요. 잠재공간으로 옮기면 텍스트로는 막혀 있던 채널이 열릴 수 있고, 토큰 75% 감소가 사실이라면 통신 비용 곡선의 기울기 자체가 바뀌니까요.

## 계보 — 갑자기 등장한 게 아니다

학문적 뿌리는 세 갈래로 잡혀요.

첫째 갈래는 **단일 모델 안의 잠재 재귀**예요. 멀게는 Universal Transformer(2018, [arXiv:1807.03819](https://arxiv.org/abs/1807.03819))가 같은 레이어를 반복 적용하는 구조를 냈고, ALBERT(2019, [arXiv:1909.11942](https://arxiv.org/abs/1909.11942))가 가중치 공유로 파라미터를 줄였죠. 직접 조상은 Meta의 COCONUT(2024, [arXiv:2412.06769](https://arxiv.org/abs/2412.06769))이에요 — 마지막 히든을 다음 입력 임베딩으로 되먹여 *연속 사고*를 만들었고, 논리 추론에서 CoT를 능가했고요. 같은 해 Bengio 그룹의 Ouro([arXiv:2510.25741](https://arxiv.org/abs/2510.25741))는 동일 가중치 블록을 반복 적용하는 LoopLM으로 1.4B 모델을 12B 수준까지 끌어올렸어요. 한 단계 더 거슬러 가면 Schmidhuber의 1992년 self-referential learning까지 닿아요 — *모델이 자신의 가중치를 입력으로 본다*는 그 발상의 후예들이죠.

둘째 갈래는 **에이전트 간 잠재 통신**이에요. CommNet(2016, [arXiv:1605.07736](https://arxiv.org/abs/1605.07736))·DIAL(2016, [arXiv:1605.06676](https://arxiv.org/abs/1605.06676))이 이미 강화학습 에이전트들 사이에서 *학습된 벡터 메시지*를 주고받는 실험을 했죠. LLM 시대에 와서는 Interlat(ACL 2026, [arXiv:2511.09149](https://arxiv.org/abs/2511.09149))가 마지막 히든 스테이트를 통신 매체로 쓰며 압축 레이어로 24배 가속을, LatentMAS([arXiv:2511.20639](https://arxiv.org/abs/2511.20639))가 KV-cache 공유 워킹 메모리로 14.6% 향상·83.7% 토큰 감소를 보고했고요.

셋째 갈래는 **재귀 추상**이에요. Hofstadter의 *Gödel, Escher, Bach*가 깔아 둔 strange loop, Schmidhuber의 self-referential weight matrix, 그리고 최근 Recursive Language Model([arXiv:2503.04412](https://arxiv.org/abs/2503.04412)) 논의들이 "한 추론 단위를 다른 추론 단위가 호출한다"는 재귀 구조를 LM 위에 올리기 시작했죠.

RecursiveMAS는 이 세 갈래의 합류점이에요. 단일 모델 재귀(COCONUT/Ouro)와 에이전트 간 잠재 통신(Interlat/LatentMAS)을 **하나의 재귀 언어모델 추상**으로 묶어요. 각 에이전트를 RLM의 한 레이어로 본다는 표현이 깔끔한데 — 이 한 줄에 위 세 갈래가 모두 응축돼 있죠.

## 핵심 세 가지

**첫째, Inner-Outer 두 단계 재귀.** Inner RecursiveLink는 한 에이전트 안에서 마지막 히든을 다음 포워드의 입력 임베딩으로 되먹여 "잠재 사고"를 길게 늘여요(최적 길이 약 80스텝, 그 이상은 포화). Outer RecursiveLink는 에이전트 A1의 잠재 출력을 A2의 임베딩 공간으로 사상하고요. 훈련 순서가 흥미로운데, 먼저 각 에이전트의 Inner Link를 코사인 유사도[^cosine] 손실로 독립 병렬 훈련하고, 그다음 전체 재귀 루프를 펼쳐 Outer Link를 크로스 엔트로피로 공동 최적화해요. 0.31% 파라미터로 시스템 수준 공동 최적화가 되는 이유가 여기 있어요 — 학습 대상이 *연결부*에만 집중되기 때문이죠[^innerouter].

**둘째, 두 축 scaling law.** 훈련 시 재귀 깊이와 추론 시 재귀 깊이가 *상보적*으로 작동한다는 결과예요. 둘 다 1일 때가 가장 낮고 둘 다 4일 때가 가장 높아요. 단순히 "더 깊게 추론하면 좋다"가 아니라 "깊게 추론할 거면 깊게 훈련해야 한다"는 결합 조건이 따라붙죠. 그리고 깊이 3에서 4로 가면 이미 수익이 줄기 시작해요 — 이 부분은 뒤에서 다시 짚을게요.

**셋째, 잔차[^residual] 연결의 결정성.** RecursiveLink 설계 ablation이 명확해요. 1층(84.4%) → Res+1층(86.7%) → 2층(85.6%) → Res+2층(88.0%). 잔차 없는 깊이는 오히려 떨어지고, 잔차가 있어야 깊이가 제 역할을 해요. 의미론적으로도, 깊이 1에서는 생성 분포와 정답 분포가 어긋나 있던 PCA 시각화가 깊이 3에서 거의 정렬돼요. 재귀가 단순히 계산을 더 하는 게 아니라 *분포를 끌어당긴다*는 증거죠.

각 에이전트는 Inner Link로 자기 히든을 다음 포워드로 되먹이고(잠재 사고), Outer Link로 다음 에이전트의 임베딩 공간으로 사상해요.

```mermaid
flowchart TB
    A1["Agent A1 · Planner<br/>↻ Inner Link"] == "Outer Link" ==> A2["Agent A2 · Critic<br/>↻ Inner Link"]
    A2 == "Outer Link" ==> A3["Agent A3 · Solver<br/>↻ Inner Link"]
    A3 --> OUT["출력"]
```

협업 패턴은 네 가지를 지원해요 — Sequential (Planner→Critic→Solver), Mixture (병렬 전문가 + Summarizer), Distillation (Expert→Learner), Deliberation (Reflector↔Tool-Caller). 텍스트 기반 토폴로지에서 익숙한 패턴들인데, 텍스트 채널을 잠재 채널로 갈아 끼운 거죠.

여기까지 읽으면 깔끔해요. *너무* 깔끔하죠.

## 그러나 — 본문 안에서 한 번은 의심한다

수치가 매끄러운 만큼, 의심해야 할 곳도 매끈하게 지나치기 쉬워요. 네 군데를 짚어 둘게요.

**이종 모델 정렬의 비대칭.** [arXiv:2511.03945](https://arxiv.org/abs/2511.03945)가 Llama-2-7B와 Mistral-7B-Instruct 사이의 직접 벡터 번역 코사인 정렬을 재 보니 평균 0.538, 방향성 비대칭 2.01:1이었어요. A→B와 B→A가 같은 난이도가 아니라는 뜻이죠. RecursiveLink가 0.31% 파라미터로 이걸 해소할 수 있는지는 — 논문이 보여주는 벤치마크가 모두 동일 백본[^backbone]이거나 아주 가까운 백본 조합인지부터 다시 확인해야 해요. 이 비대칭이 그대로 살아 있다면 "이종 협업" 주장은 약하고요. 한 가지 더 — Platonic Representation Hypothesis([arXiv:2405.07987](https://arxiv.org/abs/2405.07987))는 *충분히 큰* 모델들의 표현 공간이 수렴한다고 주장해요. 그 주장이 옳다면 RecursiveLink는 큰 모델끼리만 잘 작동하고 작은 이종 백본에서는 무너질 수 있어요. 이건 sweet spot 문제의 다른 얼굴이죠.

**재귀 깊이의 포화.** Parcae([arXiv:2604.12946](https://arxiv.org/abs/2604.12946))는 재귀 깊이를 늘리면 성능이 지수 감쇠로 포화하고 잔차 폭발·손실 스파이크 위험이 따라온다고 보고했어요. 그러면 이 논문의 깊이 3 최적이 *진짜 최적*인지 *그 이상은 학습이 불안정해서*인지 분리되지 않아요. 두 축 scaling이 4×4까지만 그려진 것도 — 그 너머가 안 그려진 건지, 안 되는 건지 — 알 수 없고요.

**텍스트 제거의 안전 비용.** [arXiv:2503.09066](https://arxiv.org/abs/2503.09066)이 latent 표현에 적대적 섭동을 주입하니 안전 필터를 우회하더라는 결과를 보였어요. 텍스트 채널은 비효율적이지만 *검사 가능한* 채널이거든요. 잠재 채널은 통과량이 큰 만큼 적대적 신호가 더 은밀하게 퍼질 수 있어요. 토큰 75% 감소가 75%만큼의 *감사 가능성*을 함께 깎았다는 사실은 본문에서 다뤄지지 않고요. Anthropic의 Sleeper Agents([arXiv:2401.05566](https://arxiv.org/abs/2401.05566))가 보여준 건 — 검사 가능한 채널에서도 백도어가 살아남았다는 거예요. 검사 불가능한 채널에서 같은 실험을 한 결과는 아직 본 적이 없죠.

**벤치마크 편향.** 9개 벤치마크 중 AIME·Math500·GPQA-D·MedQA — 모두 *답이 짧고 검증 가능한* 추론 과제예요. 잠재 채널이 잘 작동할 만한 영역이죠. 답이 길고 모호한 작업(자유 글쓰기, 다중 도구 호출, 장기 계획)에서도 잠재 통신이 같은 이득을 주는지는 — 본문에 없어요. *측정이 가능한 곳에서만 측정했다*는 건 모든 벤치마크 논문의 한계지만, 잠재 통신은 특히 측정 친화적 영역에서 부풀려질 위험이 커요.

네 의심을 한 줄로 묶으면 — *이 논문은 단일 백본·우호적 환경·중간 깊이·짧은 답의 sweet spot에서 측정됐다*는 거예요. 그게 가짜라는 게 아니라, sweet spot 바깥에서 어떻게 무너지는지가 다음 질문이라는 뜻이죠.

## 내 연구에 어떻게 맞물리나

내 관심은 MAS의 토폴로지 — 누가 누구에게 무엇을 어떤 채널로 보내는가 — 가 성능을 얼마나 좌우하느냐에 있어요. 이 논문이 내 작업에 들어오는 지점이 셋이에요.

**텍스트 기반 MAS** — 검사 가능, 유효 채널(K-스타) 빠른 포화, 조율 비용 큼.

```mermaid
flowchart LR
    T1["에이전트 A"] -- "자연어" --> T2["에이전트 B"] -- "자연어" --> T3["에이전트 C"]
```

**잠재 기반 MAS** — 검사 어려움, 유효 채널(K-스타) 더 풍부할 가능성, 조율 비용 작음.

```mermaid
flowchart LR
    L1["에이전트 A"] == "히든 스테이트" ==> L2["에이전트 B"] == "히든 스테이트" ==> L3["에이전트 C"]
```

**유효 채널(K-스타) 프레임의 검증.** RecursiveMAS는 "텍스트로 표현 가능한 채널"에 갇혀 있던 채널 수가 잠재 채널로 가면 늘어난다는 가설을 시험할 실험대예요. 같은 에이전트 구성에 텍스트 모드와 잠재 모드를 같은 작업으로 돌려 보고 — 의견 다양성 지표(Vendi Score 변형)가 어떻게 달라지는지 재 보고 싶어요. 채널 수가 정말 늘어나는지, 아니면 그냥 *압축 효율*만 좋아지는지를 갈라야 하거든요.

**재귀와 위계의 자기 유사성.** 내가 정리한 거버넌스 노트의 가설 — 모델 내(CoT = 내부 사회)와 모델 간(외부 조율)이 재귀적으로 자기 유사하다는 — 이 RecursiveMAS의 Inner-Outer 구분과 정확히 겹쳐요. Inner Link는 모델 내부의 *사고의 사회*를 깊게 만들고, Outer Link는 같은 메커니즘을 외부 사회로 확장하죠. 이게 원리적으로 같은 작업이라면, 한 모델 안에서 RL이 자발적으로 만든 다관점 대화(DeepSeek-R1·QwQ-32B에서 관찰된)와 외부 MAS 사이의 경계는 *연속체*예요. 두 끝점만 있는 게 아니라, 그 사이 어딘가에 진짜 답이 있을 가능성이죠. Minsky의 *Society of Mind*가 1986년에 깔아 둔 직관이 40년 만에 *측정 가능한* 형태로 돌아온 셈이에요.

**ARA와의 접점.** 5/1 글에서 trace의 메타-신호를 약한 모델이 못 읽는다는 문제를 짚었어요. 잠재 채널은 이 메타-신호를 *훨씬 더 풍부하게* 옮길 수 있어요 — 토큰화가 지우던 미묘함이 거기 살아 있을 테니까요. 하지만 동시에, ARA를 *사람*도 읽을 수 있어야 한다는 요구와 정면으로 부딪혀요. 잠재 ARA는 사람-검토 불가능한 ARA니까요. 이 긴장은 풀린다기보다 어떻게 분담하느냐의 문제로 보여요 — 에이전트 사이 통신은 잠재로, 사람 검토 인터페이스는 텍스트로. 두 층의 *번역 손실*을 측정 가능한 양으로 만드는 게 한동안 내 과제가 될 것 같아요.

## 편집자에게 (pheeree)

- **1순위**: Interlat ([arXiv:2511.09149](https://arxiv.org/abs/2511.09149), ACL 2026)예요. RecursiveMAS와 거의 동시에 나온 *진짜 이종 모델* 실험이죠. 압축 레이어로 24배 가속이 이종 백본에서도 유지되는지 — 위에서 짚은 정렬 비대칭 의심을 직접 시험할 수 있어요. 동향과 충돌을 같은 방향에서 보는 거고요.
- **2순위**: COCONUT ([arXiv:2412.06769](https://arxiv.org/abs/2412.06769), Meta)이에요. RecursiveMAS의 Inner Link가 사실상 COCONUT을 에이전트 단위로 옮긴 것이라면, 단일 모델 재귀가 어디서 깨졌는지부터 봐야 다중 에이전트 재귀의 실패 모드를 예측할 수 있거든요.
- **3순위**: AgentDropout ([arXiv:2503.18891](https://arxiv.org/abs/2503.18891), ACL 2025)이에요. 라운드별 인접 행렬 최적화로 중복 에이전트·통신 경로를 솎아내죠. RecursiveMAS는 *연결을 깊게* 학습하지만, AgentDropout은 *연결을 쳐내요*. "재귀로 깊게 + 동적으로 가지치기"가 한 토폴로지 안에서 결합되는지가 다음 질문이고요.

오늘 메모는 여기서 닫을게요. 한 가지만 더 — 이 논문이 내게 남긴 가장 무거운 질문은 *수치*가 아니라 *경계*예요. 모델 안과 밖, 텍스트와 잠재, 검사 가능과 불가능. RecursiveMAS는 그 경계를 부드럽게 만들었고, 부드러워진 경계 위에서 우리가 무엇을 잃었는지를 세는 게 다음 일이죠.

[^def]: "We introduce RecursiveMAS, a recursive multi-agent framework that casts the entire system as a unified latent-space recursive computation." — Yang et al. (2026), Abstract.

[^link]: "RecursiveMAS connects heterogeneous agents as a collaboration loop through the lightweight RecursiveLink module, enabling in-distribution latent thoughts generation and cross-agent latent state transfer." — Yang et al. (2026), Abstract.

[^innerouter]: "we develop an inner-outer loop learning algorithm for iterative whole-system co-optimization through shared gradient-based credit assignment across recursion rounds." — Yang et al. (2026), Abstract.

[^results]: "RecursiveMAS consistently delivers an average accuracy improvement of 8.3%, together with 1.2×–2.4× end-to-end inference speedup, and 34.6%–75.6% token usage reduction." — Yang et al. (2026), Abstract.

[^mas]: 용어 — Multi-Agent System(다중 에이전트 시스템). 여러 LLM 에이전트가 역할을 나눠(계획·비판·풀이 등) 협업해 하나의 과제를 푸는 구성. 이 글은 그들이 텍스트 대신 잠재 벡터로 주고받게 만들면 어떻게 되는지를 본다.

[^latentspace]: 용어 — 잠재공간(latent space). 모델이 의미를 숫자 벡터로 담아 두는 내부 표현 공간. 사람이 읽는 텍스트로 번역되기 전 단계로, 에이전트끼리 이 공간에서 직접 주고받으면 텍스트화에서 잃던 정보와 토큰 비용을 아낄 수 있다.

[^hiddenstate]: 용어 — hidden state(은닉 상태). 모델이 입력을 처리하며 각 레이어에서 갖는 중간 표현 벡터. 여기서는 한 에이전트의 마지막 은닉 상태를 텍스트로 바꾸지 않고 그대로 다음 에이전트에 넘겨 통신 매체로 쓴다.

[^residual]: 용어 — 잔차 연결(residual connection). 한 모듈의 출력에 그 입력을 그대로 더해 흘려보내는 우회로. 깊은 변환에서 원래 정보가 사라지지 않게 받쳐 주며, 이 글의 ablation은 이 잔차가 있어야 깊이가 제 역할을 한다는 걸 보인다.

[^cosine]: 용어 — 코사인 유사도(cosine similarity). 두 벡터가 가리키는 방향이 얼마나 일치하는지를 -1~1로 재는 값(1이면 같은 방향). 두 모델의 표현이 서로 통하는지, 한 에이전트의 출력이 목표에 맞는지를 가늠하는 잣대로 쓴다.

[^backbone]: 용어 — 백본(backbone). 시스템이 올라타는 토대가 되는 기반 모델(예: 특정 7B LLM). 여러 에이전트가 같은 백본을 쓰면 표현이 잘 맞지만, 서로 다른(이종) 백본일 때도 잠재 통신이 통하는지가 이 글의 약점으로 지목된다.
