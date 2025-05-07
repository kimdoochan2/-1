import streamlit as st
from openai import OpenAI
import tempfile

st.set_page_config(page_title="ChatPDF", layout="centered")

# --- 세션 상태 초기화 ---
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "vector_store_id" not in st.session_state:
    st.session_state.vector_store_id = None
if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None

# --- 사이드바 ---
st.sidebar.header("🔐 OpenAI API 설정")
st.session_state.api_key = st.sidebar.text_input("API Key 입력", type="password", value=st.session_state.api_key)

# Clear 버튼
if st.sidebar.button("🗑️ Clear Vector Store"):
    st.session_state.chat_history = []
    client = OpenAI(api_key=st.session_state.api_key)
    if st.session_state.vector_store_id:
        try:
            client.beta.vector_stores.delete(st.session_state.vector_store_id)
            st.success("✅ 벡터 스토어 삭제 완료")
        except Exception as e:
            st.error(f"벡터 스토어 삭제 중 오류: {e}")
    st.session_state.vector_store_id = None
    st.session_state.assistant_id = None

st.title("📄 ChatPDF - PDF 기반 챗봇")

# --- PDF 업로더 ---
uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")

# --- 질문 입력 ---
question = st.text_input("PDF에 대해 궁금한 내용을 입력하세요:")

# --- 챗봇 응답 처리 ---
def chat_with_pdf(pdf_file, query):
    client = OpenAI(api_key=st.session_state.api_key)

    # 1. 임시 파일 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_file.read())
        tmp_path = tmp.name

    # 2. 파일 업로드
    uploaded = client.files.create(file=open(tmp_path, "rb"), purpose="assistants")

    # 3. 벡터 스토어 생성 및 파일 연결
    vector_store = client.beta.vector_stores.create(name="ChatPDF VectorStore")
    client.beta.vector_stores.file_batches.upload_and_poll(vector_store.id, files=[uploaded.id])
    st.session_state.vector_store_id = vector_store.id

    # 4. Assistant 생성
    assistant = client.beta.assistants.create(
        name="PDF Chat Assistant",
        instructions="사용자가 업로드한 PDF 내용을 바탕으로 질문에 답하세요.",
        tools=[{"type": "file_search"}],
        model="gpt-4"
    )
    st.session_state.assistant_id = assistant.id

    # 5. Thread 생성 및 메시지 전송
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=query
    )

    # 6. Run 실행
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
    )

    # 7. 응답 완료까지 대기
    import time
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status == "completed":
            break
        elif run_status.status == "failed":
            return "❌ 실행 실패"
        time.sleep(1)

    # 8. 응답 출력
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    for msg in reversed(messages.data):
        if msg.role == "assistant":
            return msg.content[0].text.value
    return "❓ 응답 없음"

# --- 질문 처리 ---
if st.button("전송") and uploaded_file and question.strip():
    with st.spinner("📚 GPT가 PDF를 분석하고 있어요..."):
        response = chat_with_pdf(uploaded_file, question)
        st.session_state.chat_history.append({"question": question, "answer": response})

# --- 대화 출력 ---
for chat in st.session_state.chat_history:
    st.markdown(f"**🙋 질문:** {chat['question']}")
    st.markdown(f"**🤖 GPT 응답:** {chat['answer']}")
