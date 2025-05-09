import streamlit as st
import openai
import tempfile
import time

st.set_page_config(page_title="ChatPDF", layout="centered")

# 버전 표시 (확인용)
st.sidebar.write("📦 OpenAI 버전:", openai.__version__)

# 세션 초기화
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "vector_store_id" not in st.session_state:
    st.session_state.vector_store_id = None
if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# API 키 입력
st.sidebar.header("🔐 OpenAI 설정")
st.session_state.api_key = st.sidebar.text_input("API Key 입력", type="password", value=st.session_state.api_key)

# 벡터스토어 삭제
if st.sidebar.button("🗑️ Clear"):
    try:
        client = openai.Client(api_key=st.session_state.api_key)
        if st.session_state.vector_store_id:
            client.beta.vector_stores.delete(st.session_state.vector_store_id)
        st.success("✅ 벡터 스토어가 삭제되었습니다.")
    except Exception as e:
        st.error(f"❌ 삭제 실패: {e}")
    st.session_state.vector_store_id = None
    st.session_state.assistant_id = None
    st.session_state.chat_history = []

# UI 구성
st.title("📄 ChatPDF")
uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")
question = st.text_input("질문을 입력하세요:")

# GPT 응답 함수
def chat_with_pdf(pdf_file, query):
    try:
        client = openai.Client(api_key=st.session_state.api_key)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_file.read())
            tmp_path = tmp.name

        uploaded = client.files.create(file=open(tmp_path, "rb"), purpose="assistants")

        vector_store = client.beta.vector_stores.create(name="ChatPDF VectorStore")
        client.beta.vector_stores.file_batches.upload_and_poll(vector_store.id, files=[uploaded.id])
        st.session_state.vector_store_id = vector_store.id

        assistant = client.beta.assistants.create(
            name="PDF Assistant",
            instructions="사용자가 업로드한 PDF 파일의 내용을 바탕으로 질문에 답하세요.",
            tools=[{"type": "file_search"}],
            model="gpt-4"
        )
        st.session_state.assistant_id = assistant.id

        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=query
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
        )

        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                return "❌ 실행 실패"
            time.sleep(1)

        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for msg in reversed(messages.data):
            if msg.role == "assistant":
                return msg.content[0].text.value

        return "❓ 응답이 없습니다."
    except Exception as e:
        return f"⚠️ 오류 발생: {e}"

# 질문 전송 처리
if st.button("전송") and uploaded_file and question.strip():
    with st.spinner("📚 GPT가 PDF를 분석하고 있습니다..."):
        response = chat_with_pdf(uploaded_file, question)
        st.session_state.chat_history.append({"question": question, "answer": response})

# 대화 출력
for chat in st.session_state.chat_history:
    st.markdown(f"**🙋 질문:** {chat['question']}")
    st.markdown(f"**🤖 응답:** {chat['answer']}")
