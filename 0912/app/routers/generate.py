from fastapi import APIRouter
from pydantic import BaseModel
from app.services.llm import generate_campaign

router = APIRouter()

class GenerateRequest(BaseModel):
    name: str
    category: str
    address: str
    strengths: list[str] = []
    tone: str = "정중하고 친근한 1인칭, 이모지 1~2개"
    channels: list[str] = ["instagram","naver_blog"]
    reviews: list[str] = []  # 초기엔 수동 입력/CSV 업로드

@router.post("/campaign")
def generate_campaign_api(req: GenerateRequest):
    plan = generate_campaign(req)
    return plan
