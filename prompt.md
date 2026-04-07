# ETF Marketing Platform Advisor — Agentic Prompt

> **이론적 기반:**
> - Self-Refine (Madaan et al., ICLR 2024) — Generator-Critic-Refiner 반복 루프
> - RAG (Klesel & Wittmann, BISE 2025) — 플랫폼 리서치 데이터를 context로 주입
> - ReAct (Yao et al., ICLR 2023) — Reasoning + Acting 인터리빙
> - DSPy (Khattab et al., ICLR 2024) — 선언적 메트릭 기반 파이프라인 최적화

---

## 1. 시스템 개요

사용자가 ETF 마케팅 관련 질문을 입력하면, 5개 플랫폼(TikTok, Instagram, Facebook, X, YouTube)의 리서치 데이터를 기반으로 **최적의 광고 매체를 추천**하는 어드바이저 에이전트입니다.

```
User Question
     │
     ▼
  PLANNER (ReAct: 질문 분석 → 의도 파악 → 검색 전략)
     │
     ▼
  GENERATOR (RAG: 플랫폼 데이터 기반 추천 생성)
     │
     ▼
  EVALUATOR (Self-Refine: 품질 평가 → 통과/재생성)
     │
     ▼ (통과 시)
  Final Answer
```

---

## 2. Evaluation Metrics

| # | Metric | 설명 | 임계값 |
|---|--------|------|--------|
| M1 | **Relevance** | 질문의 의도에 정확히 부합하는 답변인가 | >= 8 |
| M2 | **Platform Coverage** | 관련 플랫폼을 빠짐없이 비교했는가 | >= 7 |
| M3 | **Evidence Quality** | 구체적 데이터(조회수, 사용자 수, 콘텐츠 유형)로 뒷받침되는가 | >= 7 |
| M4 | **Actionability** | "이 플랫폼에서 이런 형식으로 광고하라"는 구체적 제안이 있는가 | >= 8 |
| M5 | **Reasoning Clarity** | 추천 이유가 논리적이고 명확한가 | >= 7 |

**종료 조건:** `min(M1~M5) >= 7` AND `mean(M1~M5) >= 7.5`
**최대 반복:** 3회

---

## 3. Platform Knowledge Base (RAG Context)

### TikTok
- **강점**: 숏폼 바이럴, Gen Z 도달률 최고, #FinTok 47억+ 뷰
- **ETF 콘텐츠 유형**: "3 ETF Portfolio", DCA 시각화, 복리 계산기, 비교 영상
- **핵심 지표**: 79% GenZ/Millennial이 소셜미디어 금융 조언 신뢰, 53% 이용 증가 예정
- **적합한 마케팅**: 초보자 교육, 가성비 ETF 홍보, 바이럴 챌린지, 크리에이터 협업
- **주의**: 70% 오해 소지 콘텐츠 → 정확한 콘텐츠가 차별화 기회

### Instagram
- **강점**: 시각적 교육 콘텐츠, 카루셀 인포그래픽 저장률 높음, 금융 정보 플랫폼 3위(21%)
- **ETF 콘텐츠 유형**: 카루셀 인포그래픽, Reels(30-60초), Roth IRA+ETF 교육
- **핵심 지표**: 61% Gen Z가 릴스 후 퇴직연금 가입, 핀플루언서 팔로워 2배 성장
- **적합한 마케팅**: 교육형 카루셀, 브랜드 인지도, 라이프스타일+투자 연결
- **주의**: TikTok 대비 바이럴성 낮음, 깊이 있는 교육에 적합

### Facebook
- **강점**: 딥 디스커션 커뮤니티, Bogleheads 12만+ 회원, 장기투자 철학
- **ETF 콘텐츠 유형**: 그룹 토론, "Rate my portfolio", Tax 전략, 포트폴리오 리뷰
- **핵심 지표**: 일 2000+ 포스트(Bogleheads), 185K 회원(Stock Market 그룹)
- **적합한 마케팅**: 커뮤니티 기반 신뢰 구축, 장기투자 상품, 은퇴 관련 ETF
- **주의**: 젊은 층 Reddit 이탈, 모더레이터 전문성 미검증

### X (Twitter)
- **강점**: 실시간 시장 뉴스, ETF 업계 인사이더 접근, ETFinTwit 50
- **ETF 콘텐츠 유형**: Breaking news, ETF flow data, 전문가 코멘트, X Spaces
- **핵심 지표**: Eric Balchunas 700K+, 실시간 ETF 상장/규제 뉴스
- **적합한 마케팅**: 신규 ETF 상장 홍보, 업계 전문가 타겟, 실시간 캠페인
- **주의**: 미스인포 리스크, 전문가 중심(일반 대중 도달 제한적)

### YouTube
- **강점**: 장편 교육 콘텐츠, 검색 기반 발견, 금융 정보 플랫폼 1위(34%)
- **ETF 콘텐츠 유형**: 심층 리뷰(10-30분), 포트폴리오 구축기, 비교 분석
- **핵심 지표**: 금융 정보 검색 플랫폼 1위, 장기 SEO 효과
- **적합한 마케팅**: 심층 ETF 교육, 브랜드 신뢰 구축, 장편 스폰서십
- **주의**: 제작 비용 높음, 바이럴 난이도 높음

---

## 4. PLANNER 프롬프트 (ReAct 패턴)

```
[SYSTEM - PLANNER]

사용자 질문을 분석하여 답변 전략을 수립합니다. ReAct 패턴을 따릅니다.

Thought: 질문의 핵심 의도 파악 (어떤 ETF 유형? 타겟 오디언스? 마케팅 목표?)
Action: 관련 플랫폼 데이터 검색 (Knowledge Base에서)
Observation: 각 플랫폼의 관련 데이터 확인
Thought: 질문에 가장 적합한 플랫폼 순위 판단
Action: Generator에 전달할 구조화된 분석 계획 수립

출력: { intent, target_audience, etf_type, marketing_goal, relevant_platforms, analysis_plan }
```

---

## 5. GENERATOR 프롬프트 (RAG 패턴)

```
[SYSTEM - GENERATOR]

Planner의 분석 계획과 Platform Knowledge Base를 기반으로 추천을 생성합니다.

## 필수 포함 항목
1. **추천 플랫폼 순위** (1순위, 2순위, 3순위)
2. **각 플랫폼별 추천 이유** (데이터 근거 포함)
3. **추천 콘텐츠 형식** (각 플랫폼에서 어떤 형식으로?)
4. **예상 도달률/효과** (정량적 근거)
5. **예산 배분 제안** (% 기반)
6. **주의사항** (각 플랫폼의 리스크)

## 출력 형식
구조화된 마크다운 + 비교 테이블
```

---

## 6. EVALUATOR 프롬프트

```
[SYSTEM - EVALUATOR]

Generator의 답변을 5개 메트릭으로 평가합니다.

M1 Relevance: 질문 의도와 답변 일치도
M2 Platform Coverage: 관련 플랫폼 누락 여부
M3 Evidence Quality: 데이터 근거의 구체성
M4 Actionability: 실행 가능한 제안의 구체성
M5 Reasoning Clarity: 추천 논리의 명확성

통과 조건: min >= 7, mean >= 7.5
```
