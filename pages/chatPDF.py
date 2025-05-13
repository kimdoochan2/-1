import streamlit as st
from openai import OpenAI
import tempfile
import time

st.title("📄 ChatPDF (2025 공식 완전판)")

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None

if "file_id" not in st.session_state:
    st.session_state.file_id = None

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

def get_client():
    return OpenAI(api_key=st.session_state.api_key)

api_key_input = st.text_input("OpenAI API Key", type="password", value=st.session_state.api_key)
if api_key_input:
    st.session_state.api_key = api_key_input

uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])

if st.session_state.api_key and uploaded_file and not st.session_state.file_id:
    client = get_client()
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    file_response = client.files.create(
        file=open(tmp_file_path, "rb"),
        purpose="assistants"
    )
    st.session_state.file_id = file_response.id

    # ✅ 진짜 최신 방식
    assistant_response = client.beta.assistants.create(
        name="ChatPDF Assistant",
        instructions="사용자가 업로드한 PDF 파일을 참고하여 질문에 답하세요.",
        model="gpt-4o",
        tools=[{"type": "file_search", "file_search": {"files": [file_response.id]}}]
    )
    st.session_state.assistant_id = assistant_response.id

    thread_response = client.beta.threads.create()
    st.session_state.thread_id = thread_response.id

    st.success("파일과 Assistant가 준비되었습니다.")

if st.button("🧹 Clear"):
    client = get_client()
    try:
        if st.session_state.assistant_id:
            client.beta.assistants.delete(st.session_state.assistant_id)
        if st.session_state.file_id:
            client.files.delete(st.session_state.file_id)
    except Exception as e:
        st.warning(f"삭제 오류: {e}")

    for key in ["assistant_id", "file_id", "thread_id"]:
        st.session_state[key] = None
    st.rerun()

if st.session_state.assistant_id and st.session_state.thread_id:
    st.markdown("### 💬 ChatPDF와 대화")
    with st.form(key="chatpdf_form", clear_on_submit=True):
        user_input = st.text_input("질문을 입력하세요:")
        submitted = st.form_submit_button("보내기")

    if submitted and user_input:
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

        with st.spinner("Assistant가 답변 중..."):
            while True:
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id
                )
                if run_status.status == "completed":
                    break
                time.sleep(1)

        messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
        for msg in messages.data:
            if msg.role == "assistant":
                st.markdown(f"**Assistant:** {msg.content[0].text.value}")
                break
else:
    st.info("PDF 파일을 업로드하고 API Key를 입력하세요.")

