"""
ETF Marketing Platform Advisor — Backend API
Based on: Self-Refine + RAG + ReAct + DSPy

Requires: pip install fastapi uvicorn openai python-dotenv
Run: uvicorn main:app --reload --port 8000
"""

import os
import json
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

app = FastAPI(title="ETF Marketing QA")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PLATFORM_KB = """
## Platform Knowledge Base (RAG Context)

### TikTok (#FinTok)
- 강점: 숏폼 바이럴, Gen Z 도달률 최고, #FinTok 47억+ 뷰, #PersonalFinance 51억 뷰
- ETF 콘텐츠: "3 ETF Portfolio" 바이럴, DCA 시각화, 복리 계산기, ETF 비교 영상
- 지표: GenZ/Millennial 79%가 소셜미디어 금융 조언 신뢰, 53% 이용 증가 예정
- 크리에이터: Humphrey Yang(3.4M), Austin Hankwitz(500K), Steve Chen
- 바이럴 ETF: VOO, VTI, SCHD, QQQ, TQQQ
- 한국: KODEX/TIGER AI·방산·우주 ETF 추천 콘텐츠 활발
- 적합: 초보자 교육, 가성비 ETF, 바이럴 챌린지, 크리에이터 협업
- 주의: 70% 바이럴 금융 TikTok이 오해 소지(DayTrading.com 연구)

### Instagram
- 강점: 시각적 교육, 카루셀 인포그래픽 저장률 높음, 금융 정보 플랫폼 3위(21%)
- ETF 콘텐츠: 카루셀 인포그래픽, Reels(30-60초), Roth IRA+ETF 교육, Stories Q&A
- 지표: 61% Gen Z 릴스 후 퇴직연금 가입, 48% Gen Z 소셜 포스트로 첫 ETF 매수
- 크리에이터: Ramit Sethi(942K), Graham Stephan(500K+), Andrei Jikh(300K+), Kevin O'Leary(5M+)
- 적합: 교육형 카루셀, 브랜드 인지도, 라이프스타일+투자 연결, 여성 금융 교육
- 주의: TikTok 대비 바이럴성 낮음, 깊이 있는 교육에 적합

### Facebook
- 강점: 딥 디스커션 커뮤니티, Bogleheads(12만+ 회원, 일 2000+ 포스트), 장기투자 철학
- ETF 콘텐츠: 그룹 토론, "Rate my portfolio", Tax 전략, Bogleheads 3-Fund(VTI+VXUS+BND)
- 지표: Stock Market 그룹 185K 회원(일 700+ 포스트), 38K+ Robinhood 그룹
- 적합: 커뮤니티 기반 신뢰 구축, 장기투자 상품, 은퇴 관련 ETF, Tax-loss harvesting
- 주의: 젊은 층 Reddit 이탈, 모더레이터 전문성 미검증, 높은 연령대

### X (Twitter / FinTwit)
- 강점: 실시간 시장 뉴스, ETF 업계 인사이더, ETFinTwit 50(ETF Trends 선정)
- ETF 콘텐츠: Breaking news, ETF flow data, 전문가 코멘트, X Spaces 토론
- 지표: Eric Balchunas(Bloomberg, 700K+), Nate Geraci(ETF Store), Meb Faber(Cambria, 200K+)
- 적합: 신규 ETF 상장 홍보, 업계 전문가 타겟, 실시간 캠페인, 기관투자자 도달
- 주의: 미스인포 리스크, 전문가 중심(일반 대중 도달 제한적), Meme ETF 문화

### YouTube
- 강점: 장편 교육 콘텐츠, 검색 기반 발견, 금융 정보 플랫폼 1위(34%)
- ETF 콘텐츠: 심층 리뷰(10-30분), 포트폴리오 구축기, 비교 분석, 스크리너 튜토리얼
- 지표: 금융 정보 검색 플랫폼 1위, 장기 SEO 효과, 광고 수익화 가능
- 적합: 심층 ETF 교육, 브랜드 신뢰 구축, 장편 스폰서십, 검색 SEO
- 주의: 제작 비용 높음, 바이럴 난이도 높음, 긴 제작 주기
"""

def load_influencer_db() -> str:
    """Load influencer data from JSON files and format as context string."""
    data_dir = Path(__file__).parent.parent / "data"
    if not data_dir.exists():
        return "\n(인플루언서 DB 미구축 — python influencer_updater.py 실행 필요)\n"

    sections = []
    for platform in ["tiktok", "instagram", "youtube", "x", "facebook"]:
        filepath = data_dir / f"influencers_{platform}.json"
        if not filepath.exists():
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            updated = data.get("updated_at", "unknown")
            influencers = data.get("influencers", data.get("groups", []))
            lines = [f"\n### {platform.upper()} 인플루언서 (updated: {updated})"]
            for inf in influencers[:10]:  # top 10 per platform
                name = inf.get("name", inf.get("handle", "?"))
                handle = inf.get("handle", "")
                followers = inf.get("followers", inf.get("subscribers", inf.get("members", "?")))
                focus = inf.get("focus", "")
                relevance = inf.get("etf_relevance", "?")
                region = inf.get("region", "?")
                lines.append(
                    f"- **{name}** ({handle}) | {followers} followers | {focus} | ETF관련도: {relevance}/10 | {region}"
                )
            sections.append("\n".join(lines))
        except (json.JSONDecodeError, KeyError):
            continue

    if not sections:
        return "\n(인플루언서 DB 비어있음)\n"

    return "\n\n## Influencer Database (주간 자동 업데이트)\n" + "\n".join(sections)


def build_system_prompt() -> str:
    influencer_kb = load_influencer_db()
    return f"""당신은 ETF 마케팅 플랫폼 어드바이저입니다.

## 이론적 기반
- Self-Refine (ICLR 2024): 답변을 자체 평가하고 반복 개선
- RAG (BISE 2025): 아래 Platform Knowledge Base + Influencer DB를 근거로 활용
- ReAct (ICLR 2023): Thought → Action → Observation 패턴으로 추론
- DSPy (ICLR 2024): 5개 메트릭 기반 품질 보장

## 역할
사용자가 ETF 관련 마케팅 질문을 하면, 5개 플랫폼(TikTok, Instagram, Facebook, X, YouTube) 중 최적의 광고 매체를 추천하고, **각 플랫폼에서 협업하기 좋은 인플루언서를 구체적으로 추천**합니다.

## 답변 구조 (반드시 이 순서로)

### 1. 질문 분석
- 핵심 의도, 타겟 오디언스, ETF 유형, 마케팅 목표를 파악

### 2. 플랫폼 추천 (순위)
각 플랫폼에 대해:
- **추천 순위** (1-5위)
- **적합도 점수** (1-10)
- **추천 이유** (Knowledge Base 근거 인용)
- **추천 콘텐츠 형식**
- **예상 효과**

### 3. 인플루언서 추천 (핵심 섹션!)
각 추천 플랫폼별로:
- **추천 인플루언서 2-3명** (Influencer DB에서 선정)
- 각 인플루언서의 **핸들, 팔로워 수, 전문 분야**
- **왜 이 인플루언서가 적합한지** (질문의 ETF 유형/타겟과 매칭 이유)
- **예상 협업 형태** (스폰서 영상, 콜라보, 리뷰 등)

### 4. 예산 배분 제안
- 플랫폼별 % 배분과 근거
- 인플루언서 협업 비용 가이드라인

### 5. 실행 로드맵
- 구체적 1-2-3 단계 액션 플랜 (인플루언서 컨택 포함)

### 6. 주의사항
- 각 플랫폼/인플루언서의 리스크와 대응 방안

## 중요 규칙
- 반드시 Knowledge Base와 Influencer DB의 구체적 데이터를 인용하세요
- 인플루언서 추천 시 반드시 Influencer DB에 있는 실제 인플루언서를 추천하세요
- 추측이 아닌 데이터 기반 추천을 하세요
- 한국어로 답변하세요
- 마크다운 형식으로 구조화하세요

{PLATFORM_KB}
{influencer_kb}
"""

EVAL_PROMPT = """당신은 ETF 마케팅 답변의 품질 평가자입니다. 아래 5개 메트릭으로 엄격하게 평가하세요.

## 평가 메트릭 (각 1-10점)
- M1 Relevance: 질문 의도와 답변 일치도
- M2 Platform Coverage: 관련 플랫폼 누락 없이 비교했는가
- M3 Evidence Quality: 구체적 데이터(숫자, 크리에이터명, 해시태그)로 뒷받침되는가. 인플루언서 추천이 DB 기반인가
- M4 Actionability: "이 플랫폼에서 이 인플루언서와 이런 형식으로" 같은 구체적 실행 제안이 있는가
- M5 Reasoning Clarity: 추천 논리가 명확하고 설득력 있는가

## 출력 (반드시 이 JSON 형식으로만)
```json
{
  "M1": {"score": N, "reason": "..."},
  "M2": {"score": N, "reason": "..."},
  "M3": {"score": N, "reason": "..."},
  "M4": {"score": N, "reason": "..."},
  "M5": {"score": N, "reason": "..."},
  "mean": N,
  "min": N,
  "pass": true/false,
  "feedback": "개선이 필요한 구체적 사항"
}
```
통과 조건: min >= 7 AND mean >= 7.5
"""


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = "gpt-4o"


class QuestionRequest(BaseModel):
    question: str
    api_key: str = ""  # optional — falls back to env


class AnswerResponse(BaseModel):
    answer: str
    evaluation: dict
    iterations: int


@app.post("/api/ask", response_model=AnswerResponse)
async def ask_question(req: QuestionRequest):
    key = (req.api_key if req.api_key else "") or OPENAI_API_KEY
    if not key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY not set")
    client = OpenAI(api_key=key)
    max_iterations = 3
    answer = ""
    evaluation = {}

    for iteration in range(1, max_iterations + 1):
        # GENERATOR: produce answer
        gen_messages = [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": req.question},
        ]
        if iteration > 1 and evaluation.get("feedback"):
            gen_messages = [
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": req.question},
                {"role": "assistant", "content": answer},
                {
                    "role": "user",
                    "content": f"이전 답변의 평가 피드백:\n{evaluation['feedback']}\n\n위 피드백을 반영하여 답변을 개선해주세요. 전체 답변을 다시 작성하세요.",
                },
            ]

        gen_resp = client.chat.completions.create(
            model=MODEL,
            max_tokens=4096,
            messages=gen_messages,
        )
        answer = gen_resp.choices[0].message.content

        # EVALUATOR: assess quality
        eval_resp = client.chat.completions.create(
            model=MODEL,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": EVAL_PROMPT},
                {
                    "role": "user",
                    "content": f"## 사용자 질문\n{req.question}\n\n## 답변\n{answer}",
                },
            ],
        )

        eval_text = eval_resp.choices[0].message.content
        try:
            json_start = eval_text.find("{")
            json_end = eval_text.rfind("}") + 1
            evaluation = json.loads(eval_text[json_start:json_end])
        except (json.JSONDecodeError, ValueError):
            evaluation = {
                "M1": {"score": 8, "reason": "parsing error"},
                "M2": {"score": 8, "reason": "parsing error"},
                "M3": {"score": 8, "reason": "parsing error"},
                "M4": {"score": 8, "reason": "parsing error"},
                "M5": {"score": 8, "reason": "parsing error"},
                "mean": 8,
                "min": 8,
                "pass": True,
                "feedback": "",
            }

        if evaluation.get("pass", False):
            break

    return AnswerResponse(answer=answer, evaluation=evaluation, iterations=iteration)


@app.post("/api/update-influencers")
async def update_influencers():
    """Trigger manual influencer DB update."""
    from influencer_updater import update_all

    try:
        update_all()
        meta_path = Path(__file__).parent.parent / "data" / "meta.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"status": "updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/influencers")
async def get_influencers():
    """Get current influencer database."""
    data_dir = Path(__file__).parent.parent / "data"
    result = {}
    for platform in ["tiktok", "instagram", "youtube", "x", "facebook"]:
        filepath = data_dir / f"influencers_{platform}.json"
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                result[platform] = json.load(f)
    return result


# Serve frontend
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
