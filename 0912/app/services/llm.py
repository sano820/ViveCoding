import os
from typing import Dict, Any
from app.prompts import POST_PROMPT, CALENDAR_PROMPT
from app.services.calendar import suggest_slots
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def llm_complete(prompt: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":"You are a Korean marketing copywriter."},
                  {"role":"user","content":prompt}],
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()

def generate_campaign(req) -> Dict[str, Any]:
    # 1) 리뷰 요약(간단 버전: 키워드 나열)
    top_keywords = []
    for r in req.reviews[:50]:
        # 아주 단순 요약(실제는 감성/키워드 추출 파이프라인 추천)
        if "맛" in r: top_keywords.append("맛")
        if "친절" in r: top_keywords.append("친절")
    top_keywords = list(set(top_keywords)) or ["신선함","청결"]

    # 2) 채널별 문안 생성
    posts = []
    for ch in req.channels:
        prompt = POST_PROMPT.format(
            name=req.name, category=req.category, address=req.address,
            strengths=", ".join(req.strengths), tone=req.tone, channel=ch,
            keywords=", ".join(top_keywords)
        )
        body = llm_complete(prompt)
        posts.append({"channel": ch, "body": body})

    # 3) 주간 캘린더 추천(요일/시간)
    slots = suggest_slots(req.category)
    cal_prompt = CALENDAR_PROMPT.format(
        name=req.name, category=req.category, slots="\n".join(slots),
    )
    calendar_text = llm_complete(cal_prompt)

    return {
        "highlights": {"keywords": top_keywords, "strengths": req.strengths},
        "posts": posts,
        "calendar": calendar_text
    }
