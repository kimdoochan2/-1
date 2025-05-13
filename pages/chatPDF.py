import streamlit as st
import openai
import tempfile
import os

st.set_page_config(page_title="ChatPDF Assistant", page_icon="📄")
st.title("📄 ChatPDF Assistant")
st.markdown("PDF 파일을 업로드하고 내용을 기반으로 자유롭게 대화하세요.")

# ✅ 사용자로부터 API Key 입력
api_key = st.text_input("🔑 OpenAI API Key를 입력하세요", type="password")

if api_key:
    client = openai.Client(api_key=api_key)

    # ✅ 세션 상태 초기화
    if 'file_id' not in st.session_state:
        st.session_state.file_id = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # ✅ PDF 파일 업로드
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

    # ✅ Clear 버튼
    if st.button("🗑️ 초기화"):
        st.session_state.file_id = None
        st.session_state.messages = []
        st.success("초기화 완료!")

    # ✅ 파일 업로드 → OpenAI로 전송
    if uploaded_file and not st.session_state.file_id:
        st.info("파일 업로드 중...")
        st.session_state.file_id = upload_pdf(uploaded_file)
        st.success("업로드 완료! 질문을 입력하세요.")

    # ✅ 대화 입력창
    if st.session_state.file_id:
        user_input = st.text_input("💬 질문:", placeholder="문서에 대해 궁금한 점을 입력하세요.")

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})

            with st.spinner("답변 생성 중..."):
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "업로드한 PDF 파일을 참고해 답변하세요."},
                        *st.session_state.messages
                    ],
                    file_ids=[st.session_state.file_id]
                )
                answer = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.markdown(f"🤖 **답변:** {answer}")

        # ✅ 대화 기록 표시
        if st.session_state.messages:
            with st.expander("📜 대화 기록 보기", expanded=False):
                for msg in st.session_state.messages:
                    role = "👤 사용자" if msg["role"] == "user" else "🤖 Assistant"
                    st.markdown(f"**{role}:** {msg['content']}")
else:
    st.warning("👆 먼저 OpenAI API Key를 입력하세요.")
