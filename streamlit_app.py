import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="국립부경대학교 도서관 챗봇", layout="centered")

# --- 규정 텍스트 (예시, 실제 규정으로 대체 가능) ---
PKNU_LIB_RULES = """
📘 국립부경대학교 도서관 규정 요약

■ 목적 및 임무
- 도서관은 학술정보자료의 수집·정리·제공을 통해 연구와 교육을 지원함.

■ 조직 및 운영
- 도서관장은 2년 임기로 도서관 업무를 총괄하며, 도서관 운영위원회가 존재함.
- 발전계획은 5년 단위로 수립되며, 연도별 계획도 포함됨.

■ 직원 및 교육
- 사서 및 전산직원 등 전문 인력을 배치하고 연간 교육 이수 필요.

■ 자료 수집 및 관리
- 자료는 단행본, 연속간행물, 참고자료, 전자자료 등으로 분류.
- 교수·학생 수에 따른 자료 확보 기준 존재 (예: 학생 1인당 70권 이상).
- 수증, 교환 등 다양한 방식으로 자료 수집 가능.
- 기증 자료로 문고 설치 가능, 자료는 관리 후 폐기·제적 가능.

■ 시설 및 이용
- 학생 1인당 1.2㎡ 이상의 공간 확보.
- 교직원, 학생, 허가된 외부인 이용 가능.
- 개관·휴관일은 관장이 정함.

■ 대출
- 대출권한: 신분증 지참, 전임교원은 50권 90일, 학부생은 10권 14일.
- 전자책은 5권, 5일 이내로 동일 적용.
- 연속간행물, 참고자료 등은 대출 불가.

■ 반납 및 벌칙
- 연체 시 대출 정지, 자료 분실 시 동일 자료 변상 원칙.
- 질서 위반자는 도서관 이용 제한 가능.

■ 기타
- 각 기관에 자료 비치 가능, 반납 요청 가능.
- 개인정보 및 인권 보호 의무 포함.


"""

# --- 세션 상태 초기화 ---
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- 사이드바에서 API Key 입력 ---
st.sidebar.header("🔐 OpenAI 설정")
st.session_state.api_key = st.sidebar.text_input("API Key 입력", type="password", value=st.session_state.api_key)

# --- 페이지 제목 ---
st.title("📚 국립부경대학교 도서관 챗봇")

# --- Clear 버튼 ---
if st.sidebar.button("🗑️ Clear 대화"):
    st.session_state.chat_history = []
    st.experimental_rerun()

# --- 사용자 입력 ---
user_input = st.text_input("도서관에 대해 궁금한 점을 입력하세요:", key="user_input")

# --- GPT 응답 요청 함수 ---
def get_gpt_response(api_key, history):
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=history,
            temperature=0.2  # 신뢰도 높게
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ 에러: {e}"

# --- 전송 버튼 클릭 시 대화 처리 ---
if st.button("전송") and user_input.strip() != "":
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # 시스템 메시지 (도서관 규정 제공)
    system_prompt = f"""
너는 국립부경대학교 도서관 규정집을 바탕으로만 대답하는 AI 챗봇이다.
다음은 도서관 규정의 전체 내용이다:

\"\"\"
{PKNU_LIB_RULES}
\"\"\"

위 규정 외의 내용은 대답하지 말고, 모르면 "규정에 해당 내용이 없습니다."라고 답변해라.
"""

    full_history = [{"role": "system", "content": system_prompt}] + st.session_state.chat_history
    gpt_reply = get_gpt_response(st.session_state.api_key, full_history)

    st.session_state.chat_history.append({"role": "assistant", "content": gpt_reply})

# --- 대화 내역 출력 ---
for chat in st.session_state.chat_history:
    if chat["role"] == "user":
        st.markdown(f"**🙋‍♂️ 질문:** {chat['content']}")
    elif chat["role"] == "assistant":
        st.markdown(f"**📚 챗봇:** {chat['content']}")
