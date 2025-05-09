import streamlit as st
import openai
import tempfile
import time
from PyPDF2 import PdfReader

st.set_page_config(page_title="ChatPDF", layout="centered")

# --- 버전 확인
st.sidebar.write("📦 OpenAI 버전:", openai.__version__)

# --- 세션 초기화
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# --- API 키 입력
st.sidebar.header("🔐 OpenAI API 설정")
st.session_state.api_key = st.sidebar.text_input("API Key 입력", type="password", value=st.session_state.api_key)

openai.api_key = st.session_state.api_key

# --- 초기화 버튼
if st.sidebar.button("🗑️ Clear 대화"):
    st.session_state.chat_history = []
    st.session_state.pdf_text = ""
    st.success("✅ 대화가 초기화되었습니다.")

# --- 파일 업로드
st.title("📄 ChatPDF (GPT-4 기반)")
uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")
question = st.text_input("궁금한 내용을 입력하세요:")

# --- PDF에서 텍스트 추출 함수
def extract_text_from_pdf(file) -> str:
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()

# --- GPT 질문 응답 함수
def ask_gpt_question(pdf_text, question, api_key):
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "다음 PDF 내용을 바탕으로 질문에 답하세요. PDF 내용이 부족하면 '해당 내용이 없습니다.'라고 답변하세요.\n\n" + pdf_text[:6000]
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ 오류 발생: {e}"

# --- 질문 처리
if st.button("전송") and uploaded_file and question.strip():
    # PDF 텍스트 추출 (최초 한 번만)
    if not st.session_state.pdf_text:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        with open(tmp_path, "rb") as f:
            st.session_state.pdf_text = extract_text_from_pdf(f)

    answer = ask_gpt_question(st.session_state.pdf_text, question, st.session_state.api_key)
    st.session_state.chat_history.append({"question": question, "answer": answer})

# --- 대화 출력
for chat in st.session_state.chat_history:
    st.markdown(f"**🙋 질문:** {chat['question']}")
    st.markdown(f"**🤖 응답:** {chat['answer']}")
