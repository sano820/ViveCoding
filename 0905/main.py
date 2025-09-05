import os
import json
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Optional

# =========================================
# 0) 환경 로드
# =========================================
load_dotenv()  # 같은 폴더의 .env 로드

# 필수 키
GOOGLE_API_KEY      = os.getenv("GOOGLE_API_KEY")

# Kakao 토큰/설정
KAKAO_ACCESS_TOKEN  = os.getenv("KAKAO_ACCESS_TOKEN")
KAKAO_REFRESH_TOKEN = os.getenv("KAKAO_REFRESH_TOKEN")
KAKAO_REST_KEY      = os.getenv("KAKAO_REST_KEY")
KAKAO_REDIRECT_URI  = os.getenv("KAKAO_REDIRECT_URI")

# 위치 (Open-Meteo는 위경도 필요)
LAT     = os.getenv("LAT")
LON     = os.getenv("LON")

# 표시용 이름
CITY_NAME = os.getenv("CITY_NAME", "서울")

KST = timezone(timedelta(hours=9))


def require(value: Optional[str], name: str):
    if not value:
        raise RuntimeError(f".env 설정 누락: {name}")
    return value


def require_lat_lon() -> tuple[str, str]:
    """
    Open-Meteo는 위경도가 필요합니다.
    .env에 LAT/LON이 없으면 설명과 함께 에러 발생시켜 사용자에게 알립니다.
    """
    if not LAT or not LON:
        raise RuntimeError(
            "Open-Meteo 사용 시 LAT/LON이 필요합니다. "
            "예: .env에\nLAT=37.66\nLON=127.06\n을 추가하세요. (상계동 근사치)"
        )
    return LAT, LON


# =========================================
# 1) Open-Meteo (키 불필요)
# https://open-meteo.com/
# =========================================
def fetch_open_meteo_current(lat: str, lon: str) -> dict:
    """
    Open-Meteo 현재 기상 + 체감온도/습도/강수/풍속 등 수집
    API 키 불필요
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "precipitation",
            "weather_code",
            "wind_speed_10m",
        ]),
        "timezone": "Asia/Seoul",
    }
    r = requests.get(url, params=params, timeout=12)
    r.raise_for_status()
    return r.json()


# =========================================
# 2) Gemini 요약/코멘트 생성
#    - 원본 JSON을 그대로 넣고, 모델이 필요한 수치/상태를 뽑아 요약하게 함
# =========================================
def build_weather_summary(weather_json: dict, city_name: str) -> str:
    require(GOOGLE_API_KEY, "GOOGLE_API_KEY")
    genai.configure(api_key=GOOGLE_API_KEY)

    # 빠르고 저렴: gemini-1.5-flash / 더 고품질: gemini-1.5-pro
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Windows 일부 로케일에서 %-m/%-d 미지원 → 안전 처리
    try:
        today = datetime.now(KST).strftime("%-m/%-d(%a)")
    except:
        today = datetime.now(KST).strftime("%m/%d(%a)")

    prompt = f"""
너는 일기예보 요약 도우미야. 아래는 Open-Meteo의 현재 날씨 응답 JSON이야.
다음 형식을 **그대로** 한국어로, 최대 6~8줄 내로 출력해.

[오늘의 날씨] {city_name} | {today}
- 현재: (상태), 기온 X°C (체감 Y°C)
- 습도: A%, 바람: B m/s
- 강수: (가능/낮음 등 한 단어 요약)
- 우산: (필요/선택/불필요 중 하나)
- 코멘트: (하루 생활 팁 한 문장)

규칙:
- 숫자는 반올림해 깔끔히.
- 정보가 없으면 "정보 없음"으로 적어.
- 과장 없이 사실 위주, 딱딱하지 않게 간결히.

<원본 JSON>
{json.dumps(weather_json, ensure_ascii=False)}
"""
    resp = model.generate_content(
        prompt,
        generation_config={"temperature": 0.2, "max_output_tokens": 512},
    )
    text = (resp.text or "").strip()

    # 카카오 텍스트 템플릿은 1,000자 전후에서 잘릴 수 있음 → 안전하게 제한
    # 개행 normalize (CRLF/CR → LF)
    text = text.replace("\r\n", "\n").replace("\r", "\n")[:950]
    return text


# =========================================
# 3) 카카오 '나에게 보내기' — 텍스트 템플릿
# =========================================
def kakao_send_text(message: str, access_token: str) -> requests.Response:
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    template_object = {
        "object_type": "text",
        "text": message,
        "link": {"web_url": "https://www.weather.go.kr/"},
        "button_title": "자세히 보기",
    }
    data = {"template_object": json.dumps(template_object, ensure_ascii=False)}
    return requests.post(url, headers=headers, data=data, timeout=12)


# =========================================
# 4) Kakao Access Token 갱신 (+ .env에 반영)
# =========================================
def kakao_refresh_access_token() -> str:
    require(KAKAO_REFRESH_TOKEN, "KAKAO_REFRESH_TOKEN")
    require(KAKAO_REST_KEY, "KAKAO_REST_KEY")
    require(KAKAO_REDIRECT_URI, "KAKAO_REDIRECT_URI")

    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": KAKAO_REST_KEY,
        "refresh_token": KAKAO_REFRESH_TOKEN,
        "redirect_uri": KAKAO_REDIRECT_URI,
    }
    r = requests.post(url, data=data, timeout=12)
    r.raise_for_status()
    payload = r.json()
    new_access = payload.get("access_token")
    if not new_access:
        raise RuntimeError(f"카카오 토큰 갱신 실패: {payload}")

    # .env의 KAKAO_ACCESS_TOKEN 값을 교체 저장(간단 구현)
    _update_env_file("KAKAO_ACCESS_TOKEN", new_access)

    # (선택) 새 refresh_token이 오면 교체
    if "refresh_token" in payload and payload["refresh_token"]:
        _update_env_file("KAKAO_REFRESH_TOKEN", payload["refresh_token"])

    return new_access


def _update_env_file(key: str, value: str, env_path: str = ".env"):
    """ .env 파일에서 key=... 라인을 찾아 값 교체. 없으면 추가. """
    try:
        if not os.path.exists(env_path):
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(f"{key}={value}\n")
            return

        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        found = False
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                found = True
                break
        if not found:
            lines.append(f"{key}={value}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception as e:
        # .env 저장 실패는 치명적이진 않으므로 경고만
        print(f"[경고] .env 갱신 실패({key}): {e}")


# =========================================
# 5) 메인
# =========================================
def main():
    # 1) 위경도 필수 확인
    lat, lon = require_lat_lon()

    # 2) 날씨 조회 (Open-Meteo)
    weather_json = fetch_open_meteo_current(lat, lon)

    # 3) Gemini 요약/코멘트
    message = build_weather_summary(weather_json, CITY_NAME)

    # 4) 카카오 발송 (401이면 토큰 갱신 → 1회 재시도)
    require(KAKAO_ACCESS_TOKEN, "KAKAO_ACCESS_TOKEN")
    resp = kakao_send_text(message, KAKAO_ACCESS_TOKEN)

    if resp.status_code == 401:
        # 토큰 갱신 후 재시도
        new_access = kakao_refresh_access_token()
        resp = kakao_send_text(message, new_access)

    if not resp.ok:
        raise RuntimeError(f"카카오 전송 실패: {resp.status_code} {resp.text}")

    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] 카톡 전송 완료 ✔")


if __name__ == "__main__":
    main()
