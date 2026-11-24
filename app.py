import base64
from io import BytesIO
from pathlib import Path

import requests
import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError
from streamlit.errors import StreamlitSecretNotFoundError


EXAMPLE_IMAGE = Path(__file__).with_name("example-sorting.jpg")
DEFAULT_TITLE = "사진 분리수거 도우미"
DEFAULT_ICON = "♻️"


def read_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, default)
    except StreamlitSecretNotFoundError:
        return default
    return value.strip() if isinstance(value, str) else default


@st.cache_data(ttl=60, show_spinner=False)
def load_service(api_url: str) -> dict:
    response = requests.get(f"{api_url}/", timeout=(5, 15))
    response.raise_for_status()
    metadata = response.json()
    if not isinstance(metadata, dict):
        raise ValueError("서비스 정보 응답이 올바르지 않습니다.")
    fields = metadata.get("fields")
    if not isinstance(fields, list) or not fields or not all(isinstance(field, str) for field in fields):
        raise ValueError("서비스 정보에 결과 칸이 없습니다.")
    return metadata


def resize_photo(raw: bytes) -> bytes:
    with Image.open(BytesIO(raw)) as original:
        image = ImageOps.exif_transpose(original).convert("RGB")
        image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


def analyze_photo(jpeg: bytes, api_url: str, access_code: str, fields: list[str]) -> None:
    try:
        response = requests.post(
            f"{api_url}/analyze",
            json={"image_b64": base64.b64encode(jpeg).decode("ascii")},
            headers={"X-Access-Code": access_code},
            timeout=(5, 120),
        )
    except requests.Timeout:
        st.error("사진 분석 시간이 초과됐습니다. 잠시 뒤 다시 시도해 주세요.")
        return
    except requests.RequestException:
        st.error("API에 연결하지 못했습니다. 잠시 뒤 다시 시도해 주세요.")
        return

    if not response.ok:
        messages = {
            401: "Streamlit과 Vercel의 APP_ACCESS_CODE 값이 같은지 확인해 주세요.",
            422: "다른 사진으로 다시 시도해 주세요.",
            429: "분석 요청 한도에 도달했습니다. 잠시 뒤 다시 시도해 주세요.",
            503: "Vercel의 환경 변수 설정과 배포 상태를 확인해 주세요.",
        }
        message = messages.get(response.status_code, "사진을 분석하지 못했습니다.")
        st.error(f"{message} (HTTP {response.status_code})")
        return

    try:
        data = response.json()
        result = data["result"]
        if not isinstance(result, dict):
            raise ValueError("분석 결과에 항목이 없습니다.")
    except (ValueError, TypeError, KeyError):
        st.error("API 응답 형식을 확인해 주세요.")
        return

    st.subheader("분석 결과")
    st.table([{"항목": field, "내용": result.get(field, "")} for field in fields])
    tokens = data.get("tokens")
    st.caption(f"상태 200 · 사용 토큰 {tokens}" if isinstance(tokens, int) else "상태 200")


api_url = read_secret("API_URL", "http://localhost:8000").rstrip("/")
access_code = read_secret("APP_ACCESS_CODE")

try:
    info = load_service(api_url)
except (requests.RequestException, ValueError):
    info = None

title = (info or {}).get("name") or DEFAULT_TITLE
icon = (info or {}).get("icon") or DEFAULT_ICON
st.set_page_config(page_title=title, page_icon=icon)
st.title(f"{icon} {title}")
description = (info or {}).get("description") or "사진 속 물건의 재질을 알아보고 분리배출 방법을 확인하세요."
st.caption(description)

if info is None:
    st.error("API에 연결하지 못했습니다. Streamlit Secrets의 API_URL과 Vercel 배포 상태를 확인해 주세요.")
    st.stop()

if not access_code:
    st.info("사진 분석을 하려면 Streamlit Secrets에 APP_ACCESS_CODE를 설정해 주세요.")

st.caption("얼굴, 신분증, 카드 번호가 보이는 사진은 올리지 마세요.")
camera = st.camera_input("분리수거할 물건 찍기") if st.toggle("카메라 켜기") else None
upload = st.file_uploader("사진 파일 올리기", type=["jpg", "jpeg", "png", "webp"])
photo = camera if camera is not None else upload

jpeg = None
if photo is not None:
    try:
        jpeg = resize_photo(photo.getvalue())
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        st.error("사진을 열 수 없습니다. 다른 이미지 파일을 올려 주세요.")
    else:
        st.image(jpeg, width=320)

if st.button("사진 분석하기", key="analyze", type="primary", disabled=jpeg is None or not access_code):
    with st.spinner("사진을 분석하는 중입니다."):
        analyze_photo(jpeg, api_url, access_code, info["fields"])

if EXAMPLE_IMAGE.is_file() and st.button("예시 그림 분석하기", key="sample", disabled=not access_code):
    example_jpeg = resize_photo(EXAMPLE_IMAGE.read_bytes())
    st.image(example_jpeg, width=320, caption="예시 그림")
    with st.spinner("예시 그림을 분석하는 중입니다."):
        analyze_photo(example_jpeg, api_url, access_code, info["fields"])
