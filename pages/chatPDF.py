import streamlit as st
import openai
import PyPDF2
import os
import tempfile

# OpenAI API key 설정 (환경변수나 secrets 사용 권장)
openai.api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="ChatPDF Assistant", page_icon="📄")
st.title("📄 ChatPDF Assistant")
st.markdown("PDF 파일을 업로드하고 내용을 기반으로 자유롭게 대화하세요.")

# 세션 상태 초기화
if 'file_id' not in st.session_state:
    st.session_state.file_id = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

# 파일 업로더 (파일은 1개만 허용)
uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])

# PDF를 임시 파일로 저장하고 OpenAI File로 업로드
def upload_pdf_to_openai(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(file.read())
        tmp_file_path = tmp_file.name

    # 파일 업로드 (OpenAI File API)
    response = openai.files.create(file=open(tmp_file_path, "rb"), purpose="assistants")
    os.remove(tmp_file_path)  # 임시 파일 삭제
    return response.id

# Clear 버튼: file_id와 messages 모두 초기화
if st.button("🗑️ Clear (Vector Store 초기화)"):
    st.session_state.file_id = None
    st.session_state.messages = []
    st.success("Vector Store와 대화 기록이 초기화되었습니다.")

# 파일 업로드 처리
if uploaded_file is not None and st.session_state.file_id is None:
    st.info("파일을 업로드 중입니다. 잠시만 기다려주세요...")
    st.session_state.file_id = upload_pdf_to_openai(uploaded_file)
    st.success("파일 업로드 성공! 이제 질문을 입력하세요.")

# Chat 기능
if st.session_state.file_id:
    user_input = st.text_input("💬 질문을 입력하세요", placeholder="예: 이 문서의 핵심 내용은 무엇인가요?")

    if user_input:
        # 메시지 히스토리 업데이트
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.spinner("답변 생성 중..."):
            # OpenAI Assistant API (File Search 사용)
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "다음 파일 내용을 기반으로 답변하세요."},
                    *st.session_state.messages
                ],
                file_ids=[st.session_state.file_id]
            )
            answer = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.markdown(f"📝 **답변:** {answer}")

    # 대화 히스토리 출력
    if st.session_state.messages:
        with st.expander("📜 이전 대화 보기", expanded=False):
            for msg in st.session_state.messages:
                role = "👤 사용자" if msg["role"] == "user" else "🤖 Assistant"
                st.markdown(f"**{role}:** {msg['content']}")
