import streamlit as st
import cv2
import easyocr
import numpy as np
from PIL import Image

# ==========================================
# 1. 페이지 기본 설정 및 모바일 최적화 스타일
# ==========================================
st.set_page_config(page_title="농심 일부인 검증 시스템", layout="wide")

# 모바일 화면에서 버튼을 큼직하게 만들고 시인성을 높이는 가시성 커스텀
st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    /* 현장 작업용 대형 버튼 스타일 */
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
st.caption("스마트폰 기본 카메라 연동형 오날인 예방 툴 (안정성 극대화 버전)")
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

def extract_text(image):
    if image is None:
        return ""
    img_np = np.array(image)
    result = reader.readtext(img_np, detail=0)
    raw_text = "".join(result).upper()
    cleaned_text = "".join([char for char in raw_text if char.isalnum()])
    return cleaned_text

# ==========================================
# 4. 현장 작업용 투트랙(Two-track) 레이아웃 구성
# ==========================================
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🎯 1단계: [기준] 마스터 등록")
    st.info("오늘 작업할 올바른 일부인을 촬영하여 기준값으로 세팅하세요.")
    
    # 버그를 유발하던 capture 옵션을 제거하여 호환성을 100%로 올렸습니다.
    master_file = st.file_uploader(
        "📸 터치하여 [기준] 사진 촬영", 
        type=["jpg", "jpeg", "png"], 
        key="uploader_master"
    )
    
    if master_file:
        st.image(master_file, caption="🎯 현재 등록된 기준 데이터", use_container_width=True)

with col2:
    st.markdown("### 🔍 2단계: [검사] 매시간 대조")
    st.info("현재 라인에서 생산되어 나온 제품의 일부인을 촬영하세요.")
    
    test_file = st.file_uploader(
        "📸 터치하여 [검사] 사진 촬영", 
        type=["jpg", "jpeg", "png"], 
        key="uploader_test"
    )
    
    if test_file:
        st.image(test_file, caption="🔍 방금 촬영된 검사 대상", use_container_width=True)

# ==========================================
# 5. 실시간 비교 알고리즘 및 최종 판정 출력
# ==========================================
st.write("---")
st.subheader("📊 AI 1:1 대조 판정 결과")

if master_file and test_file:
    m_img = Image.open(master_file)
    t_img = Image.open(test_file)
    
    with st.spinner("AI가 마킹 문자를 분석하고 있습니다..."):
        master_text = extract_text(m_img)
        test_text = extract_text(t_img)
    
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
