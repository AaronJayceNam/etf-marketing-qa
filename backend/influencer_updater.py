"""
Weekly Influencer Database Updater
Searches for the latest ETF/finance influencers across 5 platforms
and updates the local JSON database.

Usage:
  python influencer_updater.py          # Run once
  Schedule via cron/task scheduler for weekly execution
"""

import os
import json
import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

PLATFORMS = {
    "tiktok": {
        "file": "influencers_tiktok.json",
        "prompt": """Search for the top 15+ TikTok ETF/finance influencers (US + Korea).
For each, provide: handle, name, followers, focus, etf_relevance(1-10), region(US/KR/Global), content_type, sample_content, engagement_note.
Include both English-speaking creators (#FinTok) and Korean creators (재테크/ETF추천).
Return ONLY valid JSON array.""",
    },
    "instagram": {
        "file": "influencers_instagram.json",
        "prompt": """Search for the top 15+ Instagram ETF/finance influencers (US + Korea).
For each, provide: handle, name, followers, focus, etf_relevance(1-10), region(US/KR/Global), content_type(reels/carousel/stories), sample_content, engagement_note.
Return ONLY valid JSON array.""",
    },
    "youtube": {
        "file": "influencers_youtube.json",
        "prompt": """Search for the top 15+ YouTube ETF/finance influencers (US + Korea).
For each, provide: handle, name, subscribers, focus, etf_relevance(1-10), region(US/KR/Global), content_type, sample_content, engagement_note.
Return ONLY valid JSON array.""",
    },
    "x": {
        "file": "influencers_x.json",
        "prompt": """Search for the top 12+ X(Twitter) FinTwit ETF influencers.
For each, provide: handle, name, followers, focus, etf_relevance(1-10), region(US/KR/Global), content_type, sample_content, engagement_note.
Include ETFinTwit 50 members and Bloomberg/industry figures.
Return ONLY valid JSON array.""",
    },
    "facebook": {
        "file": "influencers_facebook.json",
        "prompt": """Search for the top 8+ Facebook ETF investing groups/leaders.
For each, provide: name, group_name, members, focus, etf_relevance(1-10), content_type, engagement_note.
Include Bogleheads, FIRE groups, stock market communities.
Return ONLY valid JSON array.""",
    },
}

SYSTEM_PROMPT = """You are a financial influencer research analyst.
Your task is to provide the most up-to-date list of ETF/finance influencers on a specific platform.
Return ONLY a valid JSON array with no additional text, no markdown, no code blocks.
Use your knowledge to provide the most accurate and current data available.
Include both US/Global and Korean market influencers where applicable."""


def update_platform(platform_name: str, config: dict, client: OpenAI) -> dict:
    """Update influencer data for a single platform."""
    print(f"  Updating {platform_name}...")

    resp = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4096,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": config["prompt"]},
        ],
    )

    raw = resp.choices[0].message.content.strip()
    # Strip markdown code blocks if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    if raw.startswith("json"):
        raw = raw[4:]

    try:
        influencers = json.loads(raw.strip())
    except json.JSONDecodeError:
        print(f"  WARNING: Failed to parse {platform_name} response, keeping existing data")
        return None

    result = {
        "platform": platform_name,
        "updated_at": datetime.datetime.now().isoformat(),
        "count": len(influencers),
        "influencers": influencers,
    }

    filepath = DATA_DIR / config["file"]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  {platform_name}: {len(influencers)} influencers saved")
    return result


def update_all():
    """Update all platforms."""
    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY not set")
        return

    client = OpenAI(api_key=OPENAI_API_KEY)
    print(f"=== Influencer DB Update: {datetime.datetime.now().isoformat()} ===")

    summary = {}
    for name, config in PLATFORMS.items():
        result = update_platform(name, config, client)
        if result:
            summary[name] = result["count"]

    # Write summary
    meta = {
        "last_updated": datetime.datetime.now().isoformat(),
        "platforms": summary,
        "total_influencers": sum(summary.values()),
    }
    with open(DATA_DIR / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n=== Done: {meta['total_influencers']} total influencers across {len(summary)} platforms ===")


if __name__ == "__main__":
    update_all()
