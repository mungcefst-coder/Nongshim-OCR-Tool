import streamlit as st
import cv2
import easyocr
import numpy as np
from PIL import Image

# ==========================================
# 1. 페이지 기본 설정 및 모바일 최적화 스타일
# ==========================================
st.set_page_config(page_title="농심 일부인 검증 시스템", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    div.stButton > button {
        width: 100% !important;
        height: 60px !important;
        font-size: 20px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
    }
    .big-font-ok { 
        font-size:28px !important; 
        color: #2ecc71; 
        font-weight: bold; 
        background-color: #e8f8f5; 
        padding: 20px; 
        border-radius: 12px; 
        text-align: center; 
        border: 3px solid #2ecc71; 
    }
    .big-font-ng { 
        font-size:28px !important; 
        color: #e74c3c; 
        font-weight: bold; 
        background-color: #fadbd8; 
        padding: 20px; 
        border-radius: 12px; 
        text-align: center; 
        border: 3px solid #e74c3c; 
        animation: blinker 1.5s linear infinite;
    }
    @keyframes blinker {
        50% { opacity: 0.7; }
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 상단 헤더 영역
# ==========================================
st.image("nongshim_logo.png", width=150)
st.title("🍜 부산생산1팀 일부인 검증 시스템")
st.caption("고화질 스마트폰 촬영 대응 이미지 자동 경량화 버전 (V3.2)")
st.write("---")

# ==========================================
# 3. AI OCR 엔진 초기화
# ==========================================
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False) 

try:
    reader = load_ocr()
except Exception as e:
    st.error(f"⚠️ AI 엔진 로드 오류: {e}")

# [핵심] 고화질 이미지를 받아서 가볍게 압축 및 리사이징하는 함수
def process_and_extract_text(uploaded_file):
    if uploaded_file is None:
        return None, ""
    
    # 1. 이미지를 PIL 객체로 로드
    img = Image.open(uploaded_file)
    
    # 2. 이미지 스마트 리사이징 (가로 기준 800픽셀로 자동 축소하여 메모리 폭발 방지)
    max_width = 800
    if img.width > max_width:
        w_percent = (max_width / float(img.width))
        h_size = int((float(img.height) * float(w_percent)))
        img = img.resize((max_width, h_size), Image.Resampling.LANCZOS)
    
    # 3. AI 인식을 위해 OpenCV 포맷(Numpy)으로 변환
    img_np = np.array(img)
    
    # 4. AI 글자 추출
    result = reader.readtext(img_np, detail=0)
    raw_text = "".join(result).upper()
    cleaned_text = "".join([char for char in raw_text if char.isalnum()])
    
    return img, cleaned_text

# ==========================================
# 4. 현장 작업용 레이아웃 구성
# ==========================================
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🎯 1단계: [기준] 마스터 등록")
    st.info("오늘 작업할 올바른 일부인을 촬영하여 기준값으로 세팅하세요.")
    
    master_file = st.file_uploader(
        "📸 터치하여 [기준] 사진 촬영", 
        type=["jpg", "jpeg", "png"], 
        key="uploader_master"
    )
    
    master_img_resized = None
    master_text = ""
    if master_file:
        # 업로드 즉시 자동 압축 및 텍스트 추출 실행
        master_img_resized, master_text = process_and_extract_text(master_file)
        if master_img_resized:
            st.image(master_img_resized, caption="🎯 현재 등록된 기준 데이터 (자동 경량화 완료)", use_container_width=True)

with col2:
    st.markdown("### 🔍 2단계: [검사] 매시간 대조")
    st.info("현재 라인에서 생산되어 나온 제품의 일부인을 촬영하세요.")
    
    test_file = st.file_uploader(
        "📸 터치하여 [검사] 사진 촬영", 
        type=["jpg", "jpeg", "png"], 
        key="uploader_test"
    )
    
    test_img_resized = None
    test_text = ""
    if test_file:
        # 업로드 즉시 자동 압축 및 텍스트 추출 실행
        test_img_resized, test_text = process_and_extract_text(test_file)
        if test_img_resized:
            st.image(test_img_resized, caption="🔍 방금 촬영된 검사 대상 (자동 경량화 완료)", use_container_width=True)

# ==========================================
# 5. 실시간 비교 알고리즘 및 최종 판정 출력
# ==========================================
st.write("---")
st.subheader("📊 AI 1:1 대조 판정 결과")

if master_file and test_file:
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(label="🎯 기준 데이터 (공백 제외)", value=master_text if master_text else "인식 실패")
    with res_col2:
        st.metric(label="🔍 검사 데이터 (공백 제외)", value=test_text if test_text else "인식 실패")
    
    st.write("")
    
    if master_text == test_text and master_text != "":
        st.markdown(
            '<p class="big-font-ok">🟢 일치 (OK) <br><span style="font-size:16px; font-weight:normal;">일부인이 정상입니다. 생산을 계속 진행하세요.</span></p>', 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<p class="big-font-ng">🔴 불일치 (NG) - 오날인 위험!! <br><span style="font-size:16px; font-weight:normal;">날짜나 로트번호가 다릅니다! 마킹기 입력을 즉시 확인하세요.</span></p>', 
            unsafe_allow_html=True
        )
        if master_text == "" or test_text == "":
            st.warning("⚠️ 사진이 흐리거나 비닐 반사가 심하면 글자를 읽지 못합니다. 기본 카메라의 초점을 맞춘 뒤 다시 찍어주세요.")
else:
    st.warning("💡 판정을 시작하려면 좌측의 [기준] 등록 버튼과 우측의 [검사] 대조 버튼을 각각 눌러 촬영해 주세요.")
