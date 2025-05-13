# 📄 파일 위치 예시: pages/4_ChatPDF.py

import streamlit as st
from openai import OpenAI
import tempfile
import time

st.title("📄 ChatPDF (Assistant + File Search)")

# --- session_state 초기화 ---
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None

if "file_id" not in st.session_state:
    st.session_state.file_id = None

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# --- OpenAI client 생성 함수 ---
def get_client():
    return OpenAI(api_key=st.session_state.api_key)

# --- API Key 입력 ---
api_key_input = st.text_input(
    "OpenAI API Key를 입력하세요", 
    type="password", 
    value=st.session_state.api_key
)

if api_key_input:
    st.session_state.api_key = api_key_input

# --- 파일 업로드 ---
uploaded_file = st.file_uploader("PDF 파일을 업로드하세요 (최대 1개)", type=["pdf"])

# --- 파일 업로드 처리 ---
if st.session_state.api_key and uploaded_file and not st.session_state.file_id:
    client = get_client()
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    file = client.files.create(
        file=open(tmp_file_path, "rb"),
        purpose="assistants"
    )
    st.session_state.file_id = file.id

    assistant = client.beta.assistants.create(
        name="ChatPDF Assistant",
        instructions="사용자가 업로드한 PDF 파일을 참고하여 질문에 답하세요.",
        model="gpt-4o",
        file_ids=[file.id]   # ✅ 최신 문법: file_ids에 직접 파일 ID 할당
    )
    st.session_state.assistant_id = assistant.id

    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

    st.success("✅ 파일 업로드 및 Assistant 생성 완료!")

# --- Clear 버튼 ---
if st.button("🧹 Clear (파일 + Assistant 삭제)"):
    client = get_client()
    try:
        if st.session_state.assistant_id:
            client.beta.assistants.delete(st.session_state.assistant_id)
        if st.session_state.file_id:
            client.files.delete(st.session_state.file_id)
    except Exception as e:
        st.warning(f"삭제 중 오류: {e}")

    st.session_state.assistant_id = None
    st.session_state.file_id = None
    st.session_state.thread_id = None
    st.rerun()

# --- 대화 영역 ---
if st.session_state.assistant_id and st.session_state.thread_id:
    st.markdown("### 💬 ChatPDF와 대화")
    user_input = st.text_input("PDF 내용 기반으로 질문을 입력하세요:")

    if user_input:
        client = get_client()
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=user_input
        )

        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=st.session_state.assistant_id
        )

        with st.spinner("🤖 Assistant가 답변 중입니다..."):
            while True:
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id
                )
                if run_status.status == "completed":
                    break
                time.sleep(1)

        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )

        # 가장 최근 assistant 답변 찾기
        for msg in messages.data:
            if msg.role == "assistant":
                st.markdown(f"**🤖 Assistant:** {msg.content[0].text.value}")
                break
else:
    st.info("먼저 PDF 파일을 업로드하세요.")
