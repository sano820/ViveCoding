import streamlit as st
import requests, os, json

st.title("소상공인 마케팅 에이전트")
with st.form("gen"):
    name = st.text_input("상호명")
    category = st.text_input("업종", value="카페")
    address = st.text_input("주소")
    strengths = st.text_area("강점(콤마 구분)", "원두 직배전, 조용한 분위기, 친절")
    reviews = st.text_area("후기 몇 개 붙여넣기", "맛있어요!\n사장님이 친절해요.")
    channels = st.multiselect("채널", ["instagram","naver_blog","naver_place"], default=["instagram","naver_blog"])
    submitted = st.form_submit_button("생성")

if submitted:
    payload = {
        "name": name, "category": category, "address": address,
        "strengths": [s.strip() for s in strengths.split(",") if s.strip()],
        "tone": "정중하고 친근한 1인칭, 이모지 1~2개",
        "channels": channels,
        "reviews": [r for r in reviews.split("\n") if r.strip()]
    }
    r = requests.post(os.getenv("API_URL","http://localhost:8000") + "/generate/campaign", json=payload)
    st.subheader("결과")
    st.json(r.json())
