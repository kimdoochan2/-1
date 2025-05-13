# 📄 파일 위치 예시: pages/2_Chat.py

import streamlit as st
from openai import OpenAI

st.title("💬 OpenAI Responses 챗봇")

# --- session_state 초기화 ---
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "당신은 친절하고 정확한 AI 조수입니다."}
    ]

# --- API Key 입력 ---
api_key_input = st.text_input(
    "OpenAI API Key를 입력하세요", 
    type="password", 
    value=st.session_state.api_key
)

if api_key_input:
    st.session_state.api_key = api_key_input

# --- Clear 버튼 ---
if st.button("🧹 Clear (대화 초기화)"):
    st.session_state.messages = [
        {"role": "system", "content": "당신은 친절하고 정확한 AI 조수입니다."}
    ]
    st.rerun()

# --- 이전 대화 출력 ---
st.markdown("### 📝 대화 내용")
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.markdown(f"**🙋‍ 사용자:** {msg['content']}")
    elif msg["role"] == "assistant":
        st.markdown(f"**🤖 챗봇:** {msg['content']}")

# --- 사용자 입력 + 전송 버튼 ---
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("질문을 입력하세요:")
    submitted = st.form_submit_button("입력")

# --- OpenAI 호출 함수 ---
def get_response(api_key, chat_history):
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",  # 또는 "gpt-4.1-mini"
        messages=chat_history,
        max_tokens=500,
        temperature=0.5
    )
    return response.choices[0].message.content

# --- 입력 처리 ---
if st.session_state.api_key and submitted and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("🤖 GPT-4o가 답변 중입니다..."):
        assistant_reply = get_response(st.session_state.api_key, st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    st.rerun()
elif not st.session_state.api_key:
    st.info("먼저 OpenAI API Key를 입력하세요.")
