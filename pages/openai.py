import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS

# ------------------- Streamlit 앱 -------------------
st.set_page_config(page_title="ChatPDF", page_icon="📄")
st.title("📄 ChatPDF: PDF 문서와 대화하기 (안정화 버전)")

# ------------------- API Key 입력 -------------------
st.sidebar.header("설정")
user_api_key = st.sidebar.text_input("🔑 OpenAI API Key 입력", type="password")

if user_api_key:
    openai_client = OpenAI(api_key=user_api_key)

    if "vectorstore" not in st.session_state:
        st.session_state.vectorstore = None

    def extract_text_from_pdf(uploaded_file):
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        return text

    def create_vector_store(text):
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        texts = text_splitter.split_text(text)
        embeddings = OpenAIEmbeddings(openai_api_key=user_api_key)
        vectorstore = FAISS.from_texts(texts, embeddings)
        return vectorstore

    def chat_with_pdf(vectorstore, user_question):
        docs = vectorstore.similarity_search(user_question, k=3)
        context = "\n\n".join([doc.page_content for doc in docs])
        prompt = f"다음 문서를 참고하여 사용자의 질문에 답변하세요.\n\n문서:\n{context}\n\n질문: {user_question}\n답변:" 

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 문서를 분석해주는 유능한 어시스턴트입니다."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    uploaded_file = st.file_uploader("📥 PDF 파일 업로드 (1개만 가능)", type=["pdf"])

    if uploaded_file:
        with st.spinner("PDF 텍스트 추출 및 인덱스 생성 중..."):
            pdf_text = extract_text_from_pdf(uploaded_file)
            if pdf_text:
                vectorstore = create_vector_store(pdf_text)
                st.session_state.vectorstore = vectorstore
                st.success("✅ 문서가 성공적으로 인덱싱되었습니다. 이제 질문하세요!")
            else:
                st.error("❌ PDF에서 텍스트를 추출할 수 없습니다.")

    if st.session_state.vectorstore:
        question = st.text_input("❓ 문서 기반으로 질문하세요:")

        if question:
            with st.spinner("💡 답변 생성 중..."):
                answer = chat_with_pdf(st.session_state.vectorstore, question)
                st.markdown(f"**📋 답변:** {answer}")

        if st.button("🗑️ Clear (문서 및 인덱스 삭제)"):
            st.session_state.vectorstore = None
            st.success("🧹 문서와 인덱스가 삭제되었습니다.")

    st.info("PDF 파일을 업로드하고 문서에 대해 자유롭게 질문해 보세요.")
else:
    st.warning("🔑 먼저 사이드바에 OpenAI API Key를 입력하세요.")
