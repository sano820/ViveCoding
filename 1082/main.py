# 파일명: main_workflow.py

import time
import os
from dotenv import load_dotenv  # <--- .env 파일 로드를 위해 추가

# 개발한 모듈들을 임포트
from data_extractor import extract_text_from_url, extract_text_from_pdf
from hf_client import translate, run_agent, TRANS_KO_EN_MODEL, TRANS_EN_KO_MODEL

# --- 환경 변수 로드 ---
# 프로젝트 시작 시 .env 파일을 로드하여 HF_TOKEN을 os.environ에 설정합니다.
load_dotenv()

MAX_MODEL_INPUT_LENGTH = 15000 

def run_full_report_workflow(urls: list, pdf_paths: list, user_request: str):
    """데이터 추출부터 최종 보고서까지의 전체 워크플로우를 실행합니다."""
    
    print("--- 1. 데이터 추출 시작 ---")
    combined_source_text = ""
    
    # A. 웹 데이터 추출
    for url in urls:
        print(f"  > 크롤링: {url}")
        combined_source_text += extract_text_from_url(url) + "\n\n"
    
    # B. PDF 데이터 추출
    for path in pdf_paths:
        if not os.path.exists(path):
            print(f"⚠️ 경고: 파일이 존재하지 않습니다 - {path}")
            continue
        print(f"  > PDF 추출: {path}")
        combined_source_text += extract_text_from_pdf(path) + "\n\n"

    # 텍스트 길이 제한
    if len(combined_source_text) > MAX_MODEL_INPUT_LENGTH:
        print(f"⚠️ 경고: 추출된 텍스트가 너무 깁니다. {MAX_MODEL_INPUT_LENGTH}자로 잘라냅니다.")
        combined_source_text = combined_source_text[:MAX_MODEL_INPUT_LENGTH]

    # 에이전트에게 전달할 최종 입력 (한국어)
    korean_full_input = (
        f"USER REQUEST: {user_request}\n\n"
        f"SOURCE: {combined_source_text}"
    )
    
    print("\n--- 2. 한국어 -> 영어 번역 시작 ---")
    try:
        # 1단계: 한국어 -> 영어 번역
        english_prompt_to_agent = translate(korean_full_input, TRANS_KO_EN_MODEL)
        print("  > 번역 완료. 에이전트 추론 시작.")
    except Exception as e:
        print(f"🔴 치명적 오류: 한국어 -> 영어 번역 실패. {e}")
        return

    # 3. 에이전트 추론 (영어)
    print("\n--- 3. 에이전트 보고서 작성 (LLM 추론) ---")
    start_time = time.time()
    try:
        english_report = run_agent(english_prompt_to_agent)
        elapsed_time = time.time() - start_time
        print(f"  > 영어 보고서 작성 완료. (소요 시간: {elapsed_time:.2f}초)")
    except Exception as e:
        print(f"🔴 치명적 오류: 에이전트 추론 실패. {e}")
        return

    # 4. 영어 -> 한국어 번역
    print("\n--- 4. 최종 보고서 한국어 번역 시작 ---")
    try:
        korean_final_report = translate(english_report, TRANS_EN_KO_MODEL)
        
        print("\n-----------------------------------------------------")
        print("✅ 최종 보고서 (한국어) 생성 완료")
        print("-----------------------------------------------------")
        print(korean_final_report)
        print("-----------------------------------------------------")

        # 파일로 저장
        filename = "강의자료_참고보고서.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(korean_final_report)
        print(f"\n* 보고서가 '{filename}' 파일로 저장되었습니다.")

    except Exception as e:
        print(f"🔴 치명적 오류: 영어 -> 한국어 번역 실패. {e}")

# --- 실행 파트 ---
if __name__ == "__main__":
    
    # 🌟 여기에 실제 입력 데이터를 설정하세요 🌟
    # 1. 웹사이트 URL (실제 에이전트 개발 관련 기술 문서로 변경)
    target_urls = [
        "https://blog.langchain.dev/agent-fundamentals/",  # 예시: LangChain의 에이전트 기본 개념
        "https://arxiv.org/abs/2303.17760"                # 예시: ReAct 프레임워크 논문 링크 (크롤링 가능해야 함)
    ]
    
    # 2. PDF 파일 경로 (로컬에 파일을 다운로드하고 경로를 지정하세요)
    target_pdfs = [] 
    
    # 3. 사용자 요청 (개발자 대상을 명시)
    lecture_topic = "LangChain의 ReAct 패턴을 중심으로, AI Agent의 구성 요소와 Python 기반 개발 모듈화 방법에 대한 심화 강의 자료 초안"
    
    # 전체 워크플로우 실행
    run_full_report_workflow(target_urls, target_pdfs, lecture_topic)