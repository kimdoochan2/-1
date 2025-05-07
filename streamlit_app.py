import streamlit as st
import openai

# --- API Key 입력받기 및 session_state 저장 ---
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

st.session_state.api_key = st.text_input("🔑 OpenAI API Key 입력", type="password", value=st.session_state.api_key)

# --- 질문 입력 받기 ---
question = st.text_input("💬 질문을 입력하세요:")

# --- GPT 응답 요청 함수 (캐시됨) ---
@st.cache_data(show_spinner="GPT 응답 생성 중...")
def get_gpt_response(api_key, user_input):
    if not api_key:
        return "❌ API Key가 필요합니다."

    openai.api_key = api_key

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",  # GPT-4.1 mini 모델 이름 (2024 기준)
            messages=[
                {"role": "system", "content": "너는 친절한 AI 비서야."},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"⚠️ 에러 발생: {e}"

# --- 질문 버튼 ---
if st.button("질문하기"):
    if question.strip() == "":
        st.warning("질문을 입력하세요.")
    else:
        answer = get_gpt_response(st.session_state.api_key, question)
        st.markdown("### 🧠 GPT의 응답:")
        st.write(answer)
