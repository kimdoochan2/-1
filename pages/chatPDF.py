# 📄 파일 위치 예시: pages/4_ChatPDF.py

import streamlit as st
from openai import OpenAI
import tempfile

st.title("📄 ChatPDF with OpenAI File Search")

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
uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])

# --- 파일 업로드 처리 ---
if st.session_state.api_key and uploaded_file:
    client = get_client()
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    # PDF 파일을 OpenAI에 업로드
    file_response = client.files.create(
        file=open(tmp_file_path, "rb"),
        purpose="assistants"
    )
    st.session_state.file_id = file_response.id

    # Assistant 생성
    assistant = client.beta.assistants.create(
        name="ChatPDF Assistant",
        instructions="사용자가 업로드한 PDF 파일을 기반으로 질문에 답변하세요.",
        tools=[{"type": "file_search"}],
        file_ids=[st.session_state.file_id],
        model="gpt-4o"
    )
    st.session_state.assistant_id = assistant.id

    # Thread 생성
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

    st.success("파일 업로드 및 Assistant 생성 완료!")

# --- Clear 버튼 ---
if st.button("🧹 Clear (Vector store 삭제)"):
    client = get_client()
    if st.session_state.assistant_id:
        client.beta.assistants.delete(st.session_state.assistant_id)
    if st.session_state.file_id:
        client.files.delete(st.session_state.file_id)

    st.session_state.assistant_id = None
    st.session_state.file_id = None
    st.session_state.thread_id = None
    st.rerun()

# --- 대화 영역 ---
if st.session_state.assistant_id and st.session_state.thread_id:
    st.markdown("### 💬 ChatPDF 대화")
    user_input = st.text_input("질문을 입력하세요:")

    if user_input:
        client = get_client()
        # User Message 추가
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=user_input
        )

        # Assistant Run 시작
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=st.session_state.assistant_id
        )

        # Run 완료까지 대기
        import time
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            time.sleep(1)

        # Messages 조회
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )
        # 최근 Assistant 답변 가져오기
        for msg in messages.data:
            if msg.role == "assistant":
                st.markdown(f"**🤖 Assistant:** {msg.content[0].text.value}")
                break
else:
    st.info("먼저 PDF 파일을 업로드하세요.")
