from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_generate_campaign():
    payload = {
        "name": "카페 하루",
        "category": "카페",
        "address": "서울시 노원구",
        "strengths": ["원두 직배전","조용한 분위기"],
        "tone": "정중하고 친근한 톤",
        "channels": ["instagram"],
        "reviews": ["커피가 맛있어요", "사장님이 친절해요"]
    }
    res = client.post("/generate/campaign", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "posts" in data
