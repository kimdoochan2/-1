import streamlit as st
import openai
import tempfile
import time

st.set_page_config(page_title="ChatPDF", layout="centered")

# --- 버전 확인
st.sidebar.write("📦 OpenAI 버전:", openai.__version__)

# --- 세션 초기화
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- API 키 입력
st.sidebar.header("🔐 OpenAI API 설정")
st.session_state.api_key = st.sidebar.text_input("API Key 입력", type="password", value=st.session_state.api_key)
openai.api_key = st.session_state.api_key

# --- 초기화 버튼
if st.sidebar.button("🗑️ Clear 대화"):
    st.session_state.chat_history = []
    st.session_state.thread_id = None
    st.session_state.assistant_id = None
    st.success("✅ 대화가 초기화되었습니다.")

# --- 파일 업로드 및 질문 입력
st.title("📄 ChatPDF (GPT-4 기반)")
uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")
question = st.text_input("궁금한 내용을 입력하세요:")

# --- 어시스턴트 생성 함수
def init_assistant(file_id):
    # ✅ 디버깅 정보 출력
    st.write("✅ file_id 확인:", file_id)
    st.write("✅ file_id 타입:", type(file_id))
    st.write("✅ file_ids 포장 상태:", [file_id])

    assistant = openai.beta.assistants.create(
        name="PDF Assistant",
        instructions="사용자가 업로드한 PDF 내용을 바탕으로 질문에 답하세요.",
        model="gpt-4-turbo",
        tools=[{"type": "file_search"}],
        file_ids=[file_id]  # 반드시 리스트로
    )
    st.session_state.assistant_id = assistant.id

# --- 쓰레드 생성 함수
def init_thread():
    thread = openai.beta.threads.create()
    st.session_state.thread_id = thread.id

# --- 질문 실행 함수
def ask_question(question):
    openai.api_key = st.session_state.api_key

    openai.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=question,
    )

    run = openai.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=st.session_state.assistant_id,
    )

    with st.spinner("🤖 GPT가 응답을 생성 중입니다..."):
        while True:
            status = openai.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id,
            )
            if status.status == "completed":
                break
            elif status.status == "failed":
                return "❌ 실행 실패"
            time.sleep(1)

        messages = openai.beta.threads.messages.list(thread_id=st.session_state.thread_id)
        for msg in reversed(messages.data):
            if msg.role == "assistant":
                return msg.content[0].text.value
        return "❓ 응답 없음"

# --- 전송 버튼 눌렀을 때 처리
if st.button("전송") and uploaded_file and question.strip():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    with open(tmp_path, "rb") as f:
        uploaded = openai.files.create(file=f, purpose="assistants")

    # ✅ uploaded 객체 디버깅
    st.write("🔍 uploaded 객체:", uploaded)
    st.write("🔍 uploaded.id:", getattr(uploaded, "id", "❌ 없음"))
    st.write("🔍 uploaded 타입:", type(uploaded))

    file_id = uploaded.id if hasattr(uploaded, "id") else uploaded["id"]

    if st.session_state.assistant_id is None:
        init_assistant(file_id)
    if st.session_state.thread_id is None:
        init_thread()

    answer = ask_question(question)
    st.session_state.chat_history.append({"question": question, "answer": answer})

# --- 대화 출력
for chat in st.session_state.chat_history:
    st.markdown(f"**🙋 질문:** {chat['question']}")
    st.markdown(f"**🤖 응답:** {chat['answer']}")
