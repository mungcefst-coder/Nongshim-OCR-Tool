import streamlit as st
import cv2
import easyocr
import numpy as np
from PIL import Image

# 1. 페이지 레이아웃 및 스타일 정의
st.set_page_config(page_title="농심 일부인 오날인 검증 툴", layout="wide")
st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    .big-font-ok { font-size:28px !important; color: #2ecc71; font-weight: bold; background-color: #e8f8f5; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #2ecc71; }
    .big-font-ng { font-size:28px !important; color: #e74c3c; font-weight: bold; background-color: #fadbd8; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #e74c3c; }
    </style>
""", unsafe_allow_html=True)

st.title("🍜 수출전문공장 일부인 1:1 비교 검증 시스템")
st.caption("작업자 오날인 사고 방지를 위한 초간단 AI 대조 프로토타입")

# 2. OCR 엔진 초기화 (세션 상태를 활용해 프로그램 켤 때 딱 한 번만 로드)
@st.cache_resource
def load_ocr():
    # 사내 망에서 언어 모델 다운로드 에러가 날 경우를 대비해 로컬 구동 지향
    return easyocr.Reader(['en'], gpu=False) 

try:
    reader = load_ocr()
except Exception as e:
    st.error(f"OCR 엔진 로드 중 오류 발생: {e}")

# 3. 텍스트 추출 및 전처리 함수
def extract_text(image):
    if image is None:
        return ""
    img_np = np.array(image)
    
    # AI 글자 인식 실행
    result = reader.readtext(img_np, detail=0)
    
    # 알파벳과 숫자만 추출 (공백, 마침표, 콜론 등 완벽 제거하여 오진 방지)
    raw_text = "".join(result).upper()
    cleaned_text = "".join([char for char in raw_text if char.isalnum()])
    return cleaned_text

# 4. 2단 화면 레이아웃 구성
col1, col2 = st.columns(2)

with col1:
    st.subheader("1단계: [기준] 마스터 일부인 등록")
    st.info("정상 오더지 또는 완벽하게 인쇄된 초물(첫 제품)의 일부인을 등록하세요.")
    
    master_source = st.radio("기준 이미지 입력 방식", ["카메라 촬영", "파일 업로드"], key="master_src")
    master_img = None
    
    if master_source == "카메라 촬영":
        master_img = st.camera_input("기준 일부인 촬영", key="cam_master")
    else:
        master_img = st.file_uploader("기준 이미지 파일 선택", type=["jpg", "jpeg", "png"], key="file_master")
        if master_img:
            st.image(master_img, caption="등록된 기준 마스터", use_container_width=True)

with col2:
    st.subheader("2단계: [검사] 매시간 일부인 대조")
    st.info("현재 라인에서 생산되어 나온 제품의 일부인을 촬영하세요.")
    
    test_source = st.radio("검사 이미지 입력 방식", ["카메라 촬영", "파일 업로드"], key="test_src")
    test_img = None
    
    if test_source == "카메라 촬영":
        test_img = st.camera_input("현재 제품 일부인 촬영", key="cam_test")
    else:
        test_img = st.file_uploader("검사 이미지 파일 선택", type=["jpg", "jpeg", "png"], key="file_test")
        if test_img:
            st.image(test_img, caption="방금 촬영된 검사 대상", use_container_width=True)

# 5. 실시간 비교 및 판정 결과 출력
st.write("---")
st.subheader("3단계: AI 1:1 대조 판정 결과")

if master_img and test_img:
    m_img = Image.open(master_img)
    t_img = Image.open(test_img)
    
    with st.spinner("AI가 마킹 문자를 분석하고 있습니다..."):
        master_text = extract_text(m_img)
        test_text = extract_text(t_img)
    
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(label="🎯 기준 데이터 (알파벳/숫자)", value=master_text if master_text else "글자 인식 실패")
    with res_col2:
        st.metric(label="🔍 검사 데이터 (알파벳/숫자)", value=test_text if test_text else "글자 인식 실패")
    
    st.write("")
    
    # 최종 문자열 대조
    if master_text == test_text and master_text != "":
        st.markdown('<p class="big-font-ok">🟢 일치 (OK) <br><span style="font-size:18px;">일부인이 완벽히 일치합니다. 작업을 진행하셔도 좋습니다.</span></p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="big-font-ng">🔴 불일치 (NG) - 오날인 위험!! <br><span style="font-size:18px;">유통기한 날짜나 LOT 번호가 다릅니다! 마킹기를 즉시 확인하세요.</span></p>', unsafe_allow_html=True)
        if master_text == "" or test_text == "":
            st.warning("⚠️ 초점이 흐리거나 조명이 어두워 글자를 읽지 못했을 수 있습니다. 가이드라인에 맞춰 다시 촬영해 보세요.")
else:
    st.warning("💡 판정을 시작하려면 좌측의 [기준] 이미지와 우측의 [검사] 이미지를 카메라로 찍거나 업로드해 주세요.")
