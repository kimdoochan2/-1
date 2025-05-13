import streamlit as st
import openai
import PyPDF2
import tempfile
import os

st.set_page_config(page_title="ChatPDF Assistant", page_icon="📄")
st.title("📄 ChatPDF Assistant")
st.markdown("PDF 파일을 업로드하고 내용을 기반으로 자유롭게 대화하세요.")

# ✅ 사용자로부터 OpenAI API Key 입력 받기
api_key = st.text_input("🔑 OpenAI API Key를 입력하세요", type="password")

if api_key:
    client = openai.Client(api_key=api_key)

    if 'file_id' not in st.session_state:
        st.session_state.file_id = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    uploaded_file = st.file_uploader("📂 PDF 파일을 업로드하세요", type=["pdf"])

    def upload_pdf_to_openai(file):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file.read())
            tmp_file_path = tmp_file.name

        response = client.files.create(file=open(tmp_file_path, "rb"), purpose="assistants")
        os.remove(tmp_file_path)
        return response.id

    if st.button("🗑️ Clear (초기화)"):
        st.session_state.file_id = None
        st.session_state.messages = []
        st.success("초기화 완료!")

    if uploaded_file is not None and st.session_state.file_id is None:
        st.info("파일 업로드 중...")
        st.session_state.file_id = upload_pdf_to_openai(uploaded_file)
        st.success("업로드 성공! 질문을 입력하세요.")

    if st.session_state.file_id:
        user_input = st.text_input("💬 질문을 입력하세요", placeholder="예: 이 문서의 핵심은?")

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})

            with st.spinner("답변 생성 중..."):
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "업로드한 PDF를 참고해 답변하세요."},
                        *st.session_state.messages
                    ],
                    file_ids=[st.session_state.file_id]
                )
                answer = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.markdown(f"🤖 **답변:** {answer}")

        if st.session_state.messages:
            with st.expander("📜 대화 기록 보기", expanded=False):
                for msg in st.session_state.messages:
                    role = "👤 사용자" if msg["role"] == "user" else "🤖 Assistant"
                    st.markdown(f"**{role}:** {msg['content']}")
else:
    st.warning("👆 먼저 OpenAI API Key를 입력하세요.")
