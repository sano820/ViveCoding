# app.py
import os
import streamlit as st
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.arxiv import ArxivAPIWrapper

# =========================
# 0) 환경 로드
# =========================
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# =========================
# 1) Agent 없이 단순 검색 함수
# =========================
def tavily_search(query: str, max_results: int = 5):
    if not TAVILY_API_KEY:
        return "⚠️ TAVILY_API_KEY 없음"
    tavily = TavilySearchResults(max_results=max_results)
    return tavily.run(query)

def arxiv_search(query: str, top_k: int = 10):
    arxiv = ArxivAPIWrapper(top_k_results=top_k, load_max_docs=10)
    return arxiv.run(query)

# =========================
# 2) LLM
# =========================
def generate_article(topic, web_notes, paper_notes, model="gpt-4o-mini", temperature=0.2):
    llm = ChatOpenAI(model=model, temperature=temperature, api_key=OPENAI_API_KEY)
    system_msg = """당신은 한국어 블로거이자 SEO 전문가입니다.
주제와 자료를 바탕으로 티스토리 블로그에 바로 게시할 수 있는 마크다운 글을 작성하세요.
- 제목
- 키워드
- 개요
- 본문 (소제목 포함)
- FAQ
- 출처 링크
- 마무리"""
    user_msg = f"""
[주제]
{topic}

[웹 검색 요약]
{web_notes}

[논문 검색 요약]
{paper_notes}
"""
    resp = llm.invoke([{"role": "system", "content": system_msg},
                       {"role": "user", "content": user_msg}])
    return resp.content

# =========================
# 3) Streamlit UI
# =========================
st.set_page_config(page_title="Tistory Writer (수동 발행)", page_icon="📝", layout="wide")
st.title("📝 LangChain 블로그 초안 생성기")

with st.sidebar:
    st.header("⚙️ 설정")
    openai_model = st.selectbox("OpenAI 모델", ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"], index=0)
    temperature = st.slider("창의성(temperature)", 0.0, 1.0, 0.2, 0.1)
    max_web = st.slider("웹 검색 결과 수 (Tavily)", 3, 10, 5)
    max_papers = st.slider("논문 후보 수 (arXiv)", 1, 5, 3)

topic = st.text_area("주제/키워드 입력", height=140,
                     placeholder="예) 생성형 AI의 전자상거래 적용 사례와 한계")

if st.button("🔍 수집 & ✍️ 초안 생성", type="primary", use_container_width=True):
    if not topic.strip():
        st.error("주제를 입력하세요.")
        st.stop()

    with st.spinner("자료 수집 중..."):
        web_notes = tavily_search(topic, max_web) if TAVILY_API_KEY else "(Tavily API 키 없음)"
        paper_notes = arxiv_search(topic, max_papers)

    st.subheader("1) 자료 수집 결과")
    with st.expander("웹 검색 요약", expanded=False):
        st.json(web_notes)   # dict나 JSON 문자열이면 예쁘게 출력
    with st.expander("논문 검색 요약", expanded=False):
        st.text(paper_notes)

    with st.spinner("초안 생성 중..."):
        markdown_article = generate_article(topic, web_notes, paper_notes,
                                        model=openai_model, temperature=temperature)

    st.subheader("2) 마크다운 초안 (티스토리에 복사해 넣으세요)")
    st.text_area("마크다운 결과", value=markdown_article, height=500)

    st.info("👉 위 마크다운을 복사해서 티스토리 글쓰기 창(마크다운 모드)에 붙여넣으세요.")

