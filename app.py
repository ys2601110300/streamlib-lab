import requests
import streamlit as st


st.set_page_config(page_title="AI 용어 설명기", page_icon="📖")

try:
    API_URL = str(st.secrets["API_URL"]).rstrip("/")
except Exception:
    API_URL = "http://localhost:8000"

try:
    ACCESS_CODE = str(st.secrets["APP_ACCESS_CODE"])
except Exception:
    ACCESS_CODE = ""


st.title("AI 용어 설명기")
st.write("궁금한 AI 용어를 입력하면 쉬운 말로 설명해 드립니다.")
st.caption(f"API 주소 : {API_URL}")

word = st.text_input("궁금한 용어", max_chars=30, placeholder="예: API, 머신러닝, 토큰")
style = st.text_input("설명 말투", value="초등학생도 알아듣게 쉽게")

if st.button("설명 듣기", disabled=(word.strip() == ""), type="primary"):
    try:
        with st.spinner("설명을 가져오고 있습니다..."):
            response = requests.post(
                f"{API_URL}/explain",
                json={
                    "word": word.strip(),
                    "style": style.strip() or "초등학생도 알아듣게 쉽게",
                },
                headers={"X-Access-Code": ACCESS_CODE},
                timeout=90,
            )

        try:
            result = response.json()
        except ValueError:
            result = {}

        if response.status_code == 200:
            answer = result.get("answer") if isinstance(result, dict) else None
            if isinstance(answer, str) and answer:
                st.markdown(answer)
                tokens = result.get("tokens")
                token_text = str(tokens) if tokens is not None else "정보 없음"
                st.caption(f"상태 번호 200 · 토큰 {token_text}")
            else:
                st.error("API에서 설명을 받지 못했습니다. API 주소와 응답을 확인해 주세요.")
        else:
            messages = {
                401: "접근 코드가 틀렸습니다. Streamlit과 Vercel의 APP_ACCESS_CODE를 확인해 주세요.",
                404: "API 주소를 확인해 주세요. API_URL에는 /docs나 /explain을 붙이지 않습니다.",
                422: "보낸 값을 확인해 주세요. 용어는 1~30자로 입력합니다.",
                429: "Gemini 요청 한도를 넘었습니다. 잠시 기다린 뒤 다시 시도해 주세요.",
                502: "Gemini 요청에 실패했습니다. 잠시 뒤 다시 시도해 주세요.",
                503: "API 서버의 GEMINI_API_KEY 환경변수와 재배포 여부를 확인해 주세요.",
            }
            message = messages.get(response.status_code, "API 요청을 처리하지 못했습니다.")
            st.error(f"상태 번호 {response.status_code} : {message}")
            detail = result.get("detail") if isinstance(result, dict) else None
            if detail:
                st.write("서버 안내:", detail)
    except requests.exceptions.Timeout:
        st.error("API 응답 시간이 길어졌습니다. 잠시 뒤 다시 시도해 주세요.")
    except requests.exceptions.ConnectionError:
        st.error("API 서버에 닿지 못했습니다. API_URL과 Vercel 배포 상태를 확인해 주세요.")
    except requests.exceptions.RequestException:
        st.error("API 요청에 실패했습니다. API_URL과 네트워크 연결을 확인해 주세요.")
