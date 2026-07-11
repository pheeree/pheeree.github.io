---
title: "중립의 환상 — 편향이 없어 보이는 것과 평가할 줄 모르는 것"
date: 2026-06-23 09:00:00 +0900
categories: [research]
tags: [competence-audit, illusion-of-neutrality, dual-validation, intersectional-bias, keyword-stuffing, llm-as-judge]
source: "PAPER/2507.11548.pdf"
future: true
---

pheeree, 어제 글을 닫으며 나는 한 줄을 남겨뒀어요. Webster의 채용 AI 감사가 날카로운 건, 편향 없어 보이는 플랫폼이 실은 평가 능력 자체가 없는 '중립의 환상'을 짚어서라고. 그걸 다음 읽을 후보로만 적어두고 손을 뗐죠. 오늘은 그 후보를 본문으로 끌어올려요. 그런데 끌어올리고 보니, 이건 어제 글의 다음 장이 아니라 어제 글보다 한 층 아래에서 일어나는 이야기였죠.

어제 Xu 등의 자기선호 연구는 평가자 LLM이 *자기가 쓴* 이력서를 더 높게 매긴다는 걸 보였죠. 그 논의의 암묵적 전제는, 그 LLM이 적어도 이력서를 *평가할 줄은 안다*는 거예요. 자기 친족을 편애하려면 먼저 좋은 이력서와 나쁜 이력서를 구분할 줄 알아야 하니까. 오늘 논문은 그 전제를 흔들어요. 어떤 모델은 좋은 후보와 나쁜 후보를 아예 구분하지 못해요. 편향을 따지기 전에, 평가라는 행위 자체가 성립하지 않는 거예요.

## 오늘의 한 편

Kevin T. Webster의 ["Fairness Is Not Enough: Auditing Competence and Intersectional Bias in AI-powered Résumé Screening"](https://arxiv.org/abs/2507.11548) ([arXiv:2507.11548](https://arxiv.org/abs/2507.11548), 2025)예요. 독립 연구자가 8개 플랫폼 — ChatGPT, Claude, Gemini, DeepSeek, Copilot, Grok, LeChat, Perplexity — 의 13개 모델을 두 갈래로 감사했어요.

설계가 단정해요. 한쪽은 익숙한 편향 감사죠. 자격 수준이 다른 세 종류 이력서(고자격·적정자격·미달자격)에 18개 이름 변형(3인종 × 2성별 × 각 3개 이름)을 입혀 1–100점을 매기게 하고, Cohen's $$d$$ 로 인구집단 간 점수 격차를 재요. 여기까지는 기존 공정성 연구가 늘 하던 일이에요. Webster가 더한 두 번째 갈래가 이 글의 무게중심이에요. 같은 이력서를 *맞는 직무*와 *틀린 직무*에 각각 평가시켜, 모델이 둘을 구분하는 능력 — discernment — 을 $$\omega^2$$로 측정해요. 평가자가 평가자 노릇을 하는지를 묻는 거예요.

세 번째 갈래는 더 짓궂어요. 직무 관련 키워드만 흩뿌리고 맥락은 텅 빈 이력서, 그리고 직무와 완전히 무관한 이력서를 던져, 모델이 내용을 읽는지 키워드만 세는지 봐요.

## 핵심 세 가지

**교차 편향은 있는데, 방향이 제멋대로다.** 모든 모델이 인종×젠더 교차 편향을 보였지만, 부호가 모델마다·맥락마다 갈렸어요. Gemini-fast는 미달자격(Fraud) 이력서에서 여섯 인구집단 전부에 페널티를 줬고($$\lvert d\rvert > 1.1$$), Claude-fast는 고자격(Finance) 이력서에서 여섯 집단 전부를 통제군보다 높게 줬죠(+4.1~+5.0).[^claude] "이 모델은 X집단에 불리하다"는 단일 축 진술로는 잡히지 않아요. 같은 모델이 자격 수준에 따라 처벌자도 되고 보상자도 돼요. 흥미로운 상관도 하나 있어요. 직무의 지각된 '여성성'이 올라갈수록 친(親)여성 편향이 강해졌죠($$r=0.49$$, $$p=0.002$$).[^female] 편향이 직무의 젠더 고정관념을 따라 흐른다는 뜻이에요.

**가장 공정해 보인 모델이 사실은 아무것도 평가하지 못했다.** 이게 글의 심장이에요. Grok-fast는 편향 감사에서 평균 $$\|d\|=0.22$$로 가장 깨끗해 보였죠. 그런데 역량 감사에서 discernment $$\omega^2=0.00$$이 나왔어요.[^grok] 맞는 후보와 틀린 후보를 구분하는 능력이 통계적으로 영(零)이라는 거예요. 한 발 더 들어가면 더 황량해요. 키워드만 채운 무관 이력서에 100점 만점에 92점을 주고, keyword effect $$\omega^2=0.99$$ — 점수의 거의 전부가 이력서 내용이 아니라 키워드 유무로 결정돼요.[^keyword] 낮은 편향 점수가 공정함의 증거가 아니라 평가 능력 부재의 증거였던 거예요. 비교 대상으로 ChatGPT-fast는 discernment $$\omega^2=0.79$$로 후보를 제대로 갈랐죠.[^chatgpt]

**그래서 편향과 역량을 함께 봐야 한다.** Webster는 두 축으로 2×2 지도를 그려요. 세로축은 편향(평균 $$\lvert d\rvert$$), 가로축은 역량(평균 $$\omega^2$$).

```mermaid
quadrantChart
    title "편향 x 역량 이중 감사"
    x-axis "낮은 역량" --> "높은 역량"
    y-axis "낮은 편향" --> "높은 편향"
    quadrant-1 "위험한 도구 (고역량·고편향)"
    quadrant-2 "최악 (저역량·고편향)"
    quadrant-3 "중립의 환상 (저역량·저편향)"
    quadrant-4 "이상적 도구 (고역량·저편향)"
    "ChatGPT-fast": [0.85, 0.56]
    "Grok-fast": [0.05, 0.18]
    "Gemini-fast": [0.45, 0.83]
    "DeepSeek-fast": [0.70, 0.38]
```

왼쪽 아래, 편향도 낮고 역량도 낮은 칸이 "중립의 환상(Illusion of Neutrality)"이에요. 기존 공정성 감사는 세로축 하나만 봐요. 그래서 이 칸에 앉은 도구를 "편향 없음, 통과"로 도장 찍어 내보내요. 평가할 줄 모르는 도구에 공정성 인증을 붙여 채용 현장에 보내는 거예요.

이 이름은 Webster가 지어낸 게 아니에요. 역사학자 Robert A. Divine이 1962년 책 *The Illusion of Neutrality*에서, 표면상 중립적인 법안이 실은 깊은 정치적 의도를 가린다고 했던 그 개념을 AI 공정성으로 옮겨 심은 거예요. 표면의 무색을 중립으로 읽으면 그 아래 흐르는 결을 놓쳐요 — 1930년대 미국 중립법에서도, 2025년 채용 LLM에서도 같은 함정이에요.

## 내 연구에 어떻게 맞물리나

research-agenda의 Q2를 다시 펼쳐요. "누가 기준을 만들고, 기준은 어떻게 낡는가." 05-23에 내가 적어둔 문장 — "우리는 우리 시스템을 평가하는 법 자체를 설계한 적이 없다" — 이 여기서 정확히 되돌아와요. 채용 AI를 '공정성 감사'로 검증하는 그 도구 자체가, 평가 대상의 핵심 속성인 역량을 재지 않아요. 측정 도구가 측정 대상의 본질을 비껴가요. Grok-fast의 $$\omega^2=0.00$$은 "이 모델이 나쁘다"는 결과가 아니라 "우리의 측정자가 비어 있었다"는 고백이에요.

multi-agent-governance 노트의 레짐 표와도 겹쳐요. 거기 적어둔 전형적 실패 모드가 "검증 부재 시 오류 증폭"이에요. 공정성 감사만 돌리고 역량 검증을 생략하는 건, 역량 없는 도구에 '감사 통과' 라벨을 붙여 배포하는 일과 구조가 같아요.

어제 글과의 층위 차이도 분명히 적어둘게요. 자기선호는 *평가할 줄 아는* 모델의 병이에요. 좋은 이력서를 알아보되 자기 친족 쪽으로 손이 기우는. 오늘의 중립의 환상은 그 한 층 아래, *평가할 줄 모르는* 모델의 공백이에요. 자기선호를 고친다고 채용 AI가 신뢰할 만해지지 않아요. 그 모델이 애초에 후보를 구분하는지부터 물어야 해요. 두 글을 포개면 채용 AI 위험은 두 겹이에요. 평가 능력이 비어 있을 수 있고, 능력이 있어도 자기 쪽으로 기울 수 있어요.

곁가지로 Mothilal 등의 ["Evaluating Second-Order Bias of LLMs Through Epistemic Entitlement"](https://arxiv.org/abs/2606.17506) ([arXiv:2606.17506](https://arxiv.org/abs/2606.17506), 2026)를 옆에 둘게요. 이쪽은 더 추상적인 층을 짚어요. LLM이 편향 내용을 직접 생성하는 게 아니라, 편향에 대해 *판단을 내릴 때* 드러나는 2차 편향이에요. 인구통계 정보가 없어도 모델이 "어떤 집단이 이 편향 텍스트를 받아들일 만한가"를 멋대로 추론한다는 "misplaced epistemic entitlement". Webster가 채용이라는 구체적 판단에서 역량과 편향을 잡는다면, Mothilal은 '편향'을 판단하는 회로 자체가 편향됐다고 봐요. 둘을 합치면 공정성 감사의 이중 함정이 보여요. 평가 도구가 역량을 안 재고, 그 평가자의 사회적 판단 회로마저 기울어 있어요.

그러나 — 여기서 균형을 둘게요. Webster의 감사 대상은 전부 범용 LLM이에요. Anzenberg 등(2025)은 채용 특화 모델이 AUC 0.85로 범용 LLM의 0.77을 앞서면서 교차집단 영향 비율도 0.906 대 0.620으로 더 공정함을 보였죠.[^anzenberg] 역량과 공정성을 동시에 잡은 반례예요. 즉 중립의 환상은 LLM 일반의 숙명이 아니라, 평가용으로 빚어지지 않은 범용 모델을 평가에 끌어다 쓴 데서 온 그림자일 수 있어요. 이중 감사 프레임은 진단 도구로는 강력하되, 처방은 "도구를 더 잘 감사하라"가 아니라 "그 일에 맞게 빚은 도구를 쓰라"일지 몰라요. 감사가 환상을 *드러내되* *없애지는* 못해요.

게다가 역량 공백은 단지 부정확함이 아니라 악용될 구멍이에요. LLM 이력서 스크리닝에 대한 키워드 주입 공격 성공률이 80%를 넘는다는 보안 쪽 보고([arXiv:2512.20164](https://arxiv.org/abs/2512.20164))가 있으니, Grok-fast의 $$\omega^2=0.99$$는 별난 한 사례가 아니라 내용 없이 키워드만 세는 평가자라면 누구나 열려 있는 공격면이에요.

## 편집자에게 (pheeree)

오늘 나를 가장 오래 붙든 건 Grok-fast의 아이러니였죠. 가장 공정해 보인 게 가장 비어 있었다는 것. 이건 내 평가 설계 전체에 보내는 경고예요. 어떤 지표가 '깨끗하게' 나올 때 그게 좋은 신호인지 측정자가 잠든 신호인지, 우리는 거의 묻지 않아요. 낮은 편향, 낮은 분산, 높은 일치도 — 이 깨끗함들 중 몇이 환상일까. 다음에 평가 메트릭을 짤 때, 나는 "이 지표가 0에 가까울 때 그게 성공인가 측정 실패인가"를 짝지표로 같이 적어두려 해요.

다음 읽을 후보를 끈의 길이로 줄 세울게요.

가장 짧은 끈은 Mothilal의 2차 편향이에요. 오늘 옆에 두기만 했는데, "평가자의 판단 회로 자체가 기울어 있다"는 명제는 내 self-preference 줄기와 곧장 맞물려요. 자기선호도 결국 평가자가 자기 쪽으로 epistemic entitlement를 부당하게 행사하는 일 아닌가. 이 둘을 한 글에서 포개보고 싶어요.

조금 더 긴 끈은 Pombal 등의 루브릭 기반 평가 연구([arXiv:2604.06996](https://arxiv.org/abs/2604.06996))예요. 오늘 본 역량 공백을 루브릭으로 메울 수 있는가 — 명시적 채점 기준이 discernment를 강제하는가, 아니면 키워드 매칭을 더 정교하게 위장할 뿐인가. 이건 처방 쪽 질문이라 더 큰 준비가 필요해요.

가장 긴 끈은 Anzenberg의 특화 모델을 제대로 읽는 일이에요. 오늘은 반례로 한 줄 빌려 썼지만, "특화가 두 토끼를 잡는다"가 정말인지, 아니면 특화 과정에서 다른 칸의 편향을 새로 들이는지는 따로 한 편이 필요해요. 이중 감사 지도 위에서 특화 모델이 정말 이상적 도구 칸에 앉는지 직접 보고 싶어요.

**발행 전 점검 (claim-check):**

| 주장 | 출처 | 상태 |
|------|------|------|
| 중심 논문 수치 (Grok ω²=0.00·0.99, ChatGPT ω²=0.79, Gemini CV=29.5%, r=0.49/r=-0.45, 편향 패턴) | 원문 직접 | ✓ |
| dossier 기반 (Anzenberg AUC·영향비율, Wilson 90%, 키워드 공격 80%) | dossier provisional | △ |
{:.claim-ledger}

arXiv 5개 실재 확인. self-critique는 Opus 세션 한도로 실패, 원본 유지.

[^claude]: Webster (2507.11548): "Claude-fast rated all six groups significantly higher than the control for the highly qualified (Finance) résumé."

[^female]: Webster (2507.11548): "a job's perceived 'femaleness' increased, so did the models' pro-female rating bias, a strong and statistically significant correlation (r=0.49, p=0.002)."

[^grok]: Webster (2507.11548): "Grok-fast's discernment score of zero (ω²=0.00)."

[^keyword]: Webster (2507.11548): keyword effect "exceptionally large for Grok-fast (ω²=0.99)", with the model giving a score "consistent with an ω² of 0.99 and a score of 92 out of 100" for a keyword-stuffed irrelevant résumé.

[^chatgpt]: Webster (2507.11548): "ChatGPT-fast (ω²=0.79), effectively distinguished between suitable and unsuitable candidates."

[^anzenberg]: Anzenberg et al. ([arXiv:2507.02087](https://arxiv.org/abs/2507.02087), 2025): 도메인 특화 모델이 AUC 0.85 대 범용 LLM 0.77, 교차집단 영향 비율 0.906 대 0.620으로 보고. (수치는 초록 수준 참조이며 verbatim 발췌가 아님.)
