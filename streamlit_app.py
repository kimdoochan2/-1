import streamlit as st
import openai

st.set_page_config(page_title="GPT Chat", layout="centered")

# --- 세션 상태 초기화 ---
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- 사이드바 또는 상단 입력 (API 키) ---
st.sidebar.header("🔐 OpenAI 설정")
st.session_state.api_key = st.sidebar.text_input("API Key 입력", type="password", value=st.session_state.api_key)

# --- 페이지 이름 ---
st.title("💬 GPT Chat 페이지")

# --- Clear 버튼 ---
if st.sidebar.button("🗑️ Clear 대화"):
    st.session_state.chat_history = []
    st.experimental_rerun()

# --- 사용자 입력 받기 ---
user_input = st.text_input("당신의 메시지를 입력하세요:", key="user_input")

# --- GPT 응답 요청 함수 ---
@st.cache_data(show_spinner="🤖 GPT 응답 생성 중...")
def get_gpt_response(api_key, history):
    openai.api_key = api_key
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",
            messages=history,
            temperature=0.7
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ 에러: {e}"

# --- 대화 수행 ---
if st.button("전송") and user_input.strip() != "":
    # 사용자 메시지 추가
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # GPT 응답 받기
    gpt_reply = get_gpt_response(st.session_state.api_key, [
        {"role": "system", "content": "너는 친절한 AI 비서야."}
    ] + st.session_state.chat_history)

    # 응답 저장
    st.session_state.chat_history.append({"role": "assistant", "content": gpt_reply})

# --- 대화 출력 ---
for chat in st.session_state.chat_history:
    if chat["role"] == "user":
        st.markdown(f"**🙋‍♀️ 사용자:** {chat['content']}")
    elif chat["role"] == "assistant":
        st.markdown(f"**🤖 GPT:** {chat['content']}")
