# 파일명: data_extractor.py

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

def extract_text_from_url(url: str) -> str:
    """URL에서 텍스트를 추출합니다."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 불필요한 요소 제거
        for script in soup(["script", "style", "header", "footer", "nav"]):
            script.decompose()
            
        text = soup.get_text()
        return " ".join(text.split())
    except Exception as e:
        return f"[ERROR: 웹 크롤링 실패 - {url}: {e}]"

def extract_text_from_pdf(pdf_path: str) -> str:
    """PDF 파일에서 텍스트를 추출합니다."""
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            # 텍스트 추출이 실패할 경우를 대비하여 예외 처리
            try:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            except:
                continue
                
        return " ".join(text.split())
    except Exception as e:
        return f"[ERROR: PDF 추출 실패 - {pdf_path}: {e}]"