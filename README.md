# ETF Marketing Platform Advisor

ETF 마케팅 질문을 입력하면, 5개 플랫폼(TikTok, Instagram, Facebook, X, YouTube) 중 최적의 광고 매체를 추천하는 AI 어드바이저입니다.

## Architecture

```
User Question → FastAPI Backend → Claude API (Self-Refine Loop) → Structured Answer
                                    ↑
                           Platform Knowledge Base (RAG)
```

### Agentic Prompt Design
- **Self-Refine** (ICLR 2024): Generator → Evaluator → 반복 개선 (최대 3회)
- **RAG** (BISE 2025): 5개 플랫폼 리서치 데이터를 context로 주입
- **ReAct** (ICLR 2023): Thought → Action → Observation 추론 패턴
- **DSPy** (ICLR 2024): 5개 메트릭 기반 품질 보장

### Evaluation Metrics
| Metric | Description | Threshold |
|--------|-------------|-----------|
| M1 Relevance | 질문-답변 일치도 | >= 8 |
| M2 Coverage | 플랫폼 비교 완성도 | >= 7 |
| M3 Evidence | 데이터 근거 품질 | >= 7 |
| M4 Actionability | 실행 가능성 | >= 8 |
| M5 Clarity | 추론 명확성 | >= 7 |

Pass condition: `min >= 7 AND mean >= 7.5`

## Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Then open http://localhost:8000

## Tech Stack
- **Backend**: Python, FastAPI, Anthropic SDK
- **Frontend**: Vanilla HTML/CSS/JS
- **AI**: Claude Sonnet (Self-Refine loop)

## Project Structure
```
etf-marketing-qa/
├── README.md
├── prompt.md              # Agentic prompt design document
├── backend/
│   ├── main.py            # FastAPI server + Claude API integration
│   └── requirements.txt
└── frontend/
    └── index.html         # Single-page application
```
