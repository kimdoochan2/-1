# 📄 파일 위치: pages/3_ChatGPT_질문응답.py

import streamlit as st
import openai

st.title("🤖 GPT-4.1-mini 질문 응답 챗봇")

# --- API Key 입력 및 session_state 저장 ---
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

api_key_input = st.text_input("OpenAI API Key를 입력하세요", 
                              type="password", 
                              value=st.session_state.api_key)

if api_key_input:
    st.session_state.api_key = api_key_input

# --- 사용자 질문 입력 ---
question = st.text_input("질문을 입력하세요:")

# --- GPT 호출 함수 (캐싱 사용) ---
@st.cache_data(show_spinner="GPT-4.1-mini가 답변을 생성 중입니다...")
def get_gpt_answer(api_key, user_question):
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-4o",  # 또는 gpt-4.1-mini가 정식 모델명이면 변경
        messages=[
            {"role": "system", "content": "당신은 친절하고 정확한 AI 조수입니다."},
            {"role": "user", "content": user_question}
        ],
        max_tokens=500,
        temperature=0.5
    )
    return response['choices'][0]['message']['content']

# --- 실행 ---
if st.session_state.api_key and question:
    try:
        answer = get_gpt_answer(st.session_state.api_key, question)
        st.markdown(f"**답변:** {answer}")
    except Exception as e:
        st.error(f"에러 발생: {e}")
elif not st.session_state.api_key:
    st.info("먼저 OpenAI API Key를 입력하세요.")
