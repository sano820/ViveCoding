# 파일명: hf_client.py

import requests
import os
from prompts import SYSTEM_PROMPT  # <--- prompts.py에서 시스템 프롬프트 임포트
from typing import Dict, Any, List

# --- API 설정 ---
# HF_TOKEN은 이제 os.environ에서 직접 가져옵니다. main_workflow.py에서 .env를 로드합니다.
HF_TOKEN = os.environ.get("HF_TOKEN") 
API_URL = "https://api-inference.huggingface.co/models/"

# 모델 ID
TRANS_KO_EN_MODEL = "Helsinki-NLP/opus-mt-ko-en"
TRANS_EN_KO_MODEL = "Helsinki-NLP/opus-mt-en-ko"
AGENT_MODEL = "mistralai/Mistral-7B-Instruct-v0.2" 

def _get_headers() -> Dict[str, str]:
    """API 헤더를 생성하고 토큰 누락 여부를 확인합니다."""
    if not HF_TOKEN:
        # 이 시점에서 토큰이 없으면 오류 발생
        raise ValueError("HF_TOKEN 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
    return {"Authorization": f"Bearer {HF_TOKEN}"}

def _query_hf_api(model_id: str, payload: dict) -> List[Dict[str, Any]]:
    """Hugging Face Inference API를 호출하여 JSON 결과를 반환합니다."""
    response = requests.post(API_URL + model_id, headers=_get_headers(), json=payload)
    response.raise_for_status() 
    return response.json()

def translate(text: str, source_model: str) -> str:
    """특정 번역 모델을 사용하여 텍스트를 번역합니다."""
    payload = {"inputs": text}
    result = _query_hf_api(source_model, payload)
    return result[0]['translation_text'].strip()

def run_agent(english_input: str) -> str:
    """에이전트 모델을 호출하여 영어로 된 보고서를 생성합니다."""
    
    # Mistral 모델에 맞는 인스트럭션 템플릿 사용 (SYSTEM_PROMPT 사용)
    formatted_input = f"<s>[INST] {SYSTEM_PROMPT}\n\n{english_input} [/INST]"

    payload = {
        "inputs": formatted_input,
        "parameters": {
            "max_new_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
            "return_full_text": False
        },
        "options": {"use_cache": False} 
    }
    
    result = _query_hf_api(AGENT_MODEL, payload)
    
    generated_text = result[0]['generated_text']
    return generated_text.strip().lstrip()