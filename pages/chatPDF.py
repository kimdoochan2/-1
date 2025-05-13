import streamlit as st
import openai
import tempfile
import os
import time

st.set_page_config(page_title="ChatPDF Assistant", page_icon="📄")
st.title("📄 ChatPDF Assistant")
st.markdown("PDF 파일을 업로드하고 내용을 기반으로 자유롭게 대화하세요.")

api_key = st.text_input("🔑 OpenAI API Key를 입력하세요", type="password")

if api_key:
    client = openai.Client(api_key=api_key)

    if 'file_id' not in st.session_state:
        st.session_state.file_id = None
    if 'assistant_id' not in st.session_state:
        st.session_state.assistant_id = None
    if 'thread_id' not in st.session_state:
        st.session_state.thread_id = None

    uploaded_file = st.file_uploader("📂 PDF 파일을 업로드하세요", type=["pdf"])

    def upload_pdf(file):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file.read())
            tmp_file_path = tmp_file.name

        response = client.files.create(
            file=open(tmp_file_path, "rb"),
            purpose="assistants"
        )
        os.remove(tmp_file_path)
        return response.id

    if st.button("🗑️ 초기화"):
        st.session_state.file_id = None
        st.session_state.assistant_id = None
        st.session_state.thread_id = None
        st.success("초기화 완료!")

    if uploaded_file and not st.session_state.file_id:
        st.info("파일 업로드 중...")
        st.session_state.file_id = upload_pdf(uploaded_file)
        st.success("파일 업로드 성공!")

        # ✅ Assistant 생성
        assistant = client.beta.assistants.create(
            name="ChatPDF Assistant",
            instructions="업로드된 PDF 파일을 기반으로 질문에 답하세요.",
            model="gpt-4o",
            tools=[{"type": "file_search"}]
        )
        st.session_state.assistant_id = assistant.id

        # ✅ Thread 생성
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    if st.session_state.file_id and st.session_state.assistant_id and st.session_state.thread_id:
        user_input = st.text_input("💬 질문:", placeholder="문서에 대해 궁금한 점을 입력하세요.")

        if user_input:
            client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                role="user",
                content=user_input,
                attachments=[{"file_id": st.session_state.file_id, "tools": [{"type": "file_search"}]}]
            )

            run = client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id,
                assistant_id=st.session_state.assistant_id
            )

            with st.spinner("답변 생성 중..."):
                while run.status not in ["completed", "failed", "cancelled"]:
                    time.sleep(1)
                    run = client.beta.threads.runs.retrieve(
                        thread_id=st.session_state.thread_id,
                        run_id=run.id
                    )

                if run.status == "completed":
                    messages = client.beta.threads.messages.list(
                        thread_id=st.session_state.thread_id
                    )
                    answer = messages.data[0].content[0].text.value
                    st.markdown(f"🤖 **답변:** {answer}")
                else:
                    st.error(f"실패: {run.status}")
else:
    st.warning("👆 먼저 OpenAI API Key를 입력하세요.")
