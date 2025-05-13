import streamlit as st
import openai

st.set_page_config(page_title="GPT-4.1-mini Q&A", page_icon="🤖")
st.title("🤖 GPT-4.1-mini 질문 응답기")

# API Key 입력받고 session_state에 저장
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = ''

st.session_state['api_key'] = st.text_input(
    label="OpenAI API Key를 입력하세요",
    value=st.session_state['api_key'],
    type="password"
)

# API Key 설정
if st.session_state['api_key']:
    openai.api_key = st.session_state['api_key']

    # 사용자 질문 입력
    question = st.text_input("질문을 입력하세요:")

    @st.cache_data(show_spinner="모델이 응답 중입니다...", experimental_allow_widgets=True)
    def get_gpt_response(prompt, api_key):
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",  # gpt-4.1-mini 대체 모델 이름
            messages=[
                {"role": "system", "content": "당신은 도움이 되는 AI 어시스턴트입니다."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()

    if question:
        try:
            response_text = get_gpt_response(question, st.session_state['api_key'])
            st.markdown("### 💡 GPT-4.1-mini의 답변")
            st.write(response_text)
        except Exception as e:
            st.error(f"오류 발생: {e}")
else:
    st.warning("먼저 OpenAI API Key를 입력하세요.")
