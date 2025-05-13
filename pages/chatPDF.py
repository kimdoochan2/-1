import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI

# ------------------- 설정 -------------------
openai_api_key = st.secrets["openai_api_key"]  # GitHub에 올릴 때 secrets 사용
openai_client = OpenAI(api_key=openai_api_key)

# ------------------- 함수 정의 -------------------
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def create_vector_store(text, file_name):
    file = openai_client.files.create(
        file=(file_name, text.encode("utf-8")),
        purpose="file_search"
    )
    return file.id

def delete_vector_store(file_id):
    openai_client.files.delete(file_id)

def chat_with_file(file_id, user_question):
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for reading documents."},
            {"role": "user", "content": user_question}
        ],
        file_ids=[file_id]
    )
    return response.choices[0].message.content

# ------------------- Streamlit 앱 -------------------
st.title("📄 ChatPDF: PDF로 대화하기")

if "file_id" not in st.session_state:
    st.session_state.file_id = None

uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])

if uploaded_file:
    with st.spinner("PDF 파일 읽는 중..."):
        pdf_text = extract_text_from_pdf(uploaded_file)
        file_id = create_vector_store(pdf_text, uploaded_file.name)
        st.session_state.file_id = file_id
        st.success("벡터 스토어 생성 완료. 질문을 입력하세요!")

if st.session_state.file_id:
    question = st.text_input("PDF에 대해 질문하세요")

    if question:
        with st.spinner("답변 생성 중..."):
            answer = chat_with_file(st.session_state.file_id, question)
            st.markdown(f"**답변:** {answer}")

    if st.button("Clear (벡터 스토어 삭제)"):
        delete_vector_store(st.session_state.file_id)
        st.session_state.file_id = None
        st.success("벡터 스토어가 삭제되었습니다.")

st.info("PDF를 업로드 후 질문을 입력하세요. GPT가 문서 기반으로 답변합니다.")
