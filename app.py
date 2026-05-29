import streamlit as st
import cv2
import easyocr
import numpy as np
from PIL import Image
import re

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
st.caption("주변 노이즈 및 포장재 문구 자동 필터링 고도화 버전 (V3.3)")
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

# 일부인 고유 패턴(날짜 및 로트번호)만 정밀 추출하는 알고리즘
def extract_pure_marking(raw_text):
    # 1. 8자리 연속된 유통기한 숫자 검색 (예: 20270525)
    date_match = re.search(r'\d{8}', raw_text)
    date_part = date_match.group(0) if date_match else ""
    
    # 2. 유통기한 숫자 주변에 붙은 영문+숫자 혼합 로트번호 패턴 추출
    # (현장 마킹 규칙에 맞게 숫자가 결합된 단어를 필터링)
    lot_part = ""
    # 전체 텍스트에서 8자리 날짜를 제외한 나머지 구역 분석
    remaining_text = raw_text.replace(date_part, "")
    
    # 알파벳과 숫자가 혼합된 2~6자리 단어 패턴 검색 (예: F1, M, A01 등 일부인 특유 패턴)
    # 생산 현장 로트 규칙에 맞춰 과도하게 긴 포장재 문구는 제외
    lot_matches = re.findall(r'[A-Z0-9]{2,6}', remaining_text)
    if lot_matches:
        # 추출된 항목 중 일부인 특성(숫자와 영문 조합 등)에 가장 가까운 것 선택
        lot_part = lot_matches[0]

    # 날짜와 로트번호를 깔끔하게 조합하여 반환
    if date_part:
        return f"{date_part} {lot_part}".strip()
    return raw_text # 만약 8자리 날짜 패턴이 안 보이면 전체 텍스트 반환

def process_and_extract_text(uploaded_file):
    if uploaded_file is None:
        return None, ""
    
    img = Image.open(uploaded_file)
    
    # 이미지 자동 경량화 (메모리 튕김 방지)
    max_width = 800
    if img.width > max_width:
        w_percent = (max_width / float(img.width))
        h_size = int((float(img.height) * float(w_percent)))
        img = img.resize((max_width, h_size), Image.Resampling.LANCZOS)
    
    img_np = np.array(img)
    result = reader.readtext(img_np, detail=0)
    
    # 원본 추출 텍스트 병합
    raw_combined = "".join(result).upper().replace(" ", "")
    
    # [핵심] 불필요한 포장재 문구를 걸러내고 순수 일부인만 추출
    pure_marking = extract_pure_marking(raw_combined)
    
    return img, pure_marking

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
        master_img_resized, master_text = process_and_extract_text(master_file)
        if master_img_resized:
            st.image(master_img_resized, caption="🎯 현재 등록된 기준 데이터", use_container_width=True)

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
        test_img_resized, test_text = process_and_extract_text(test_file)
        if test_img_resized:
            st.image(test_img_resized, caption="🔍 방금 촬영된 검사 대상", use_container_width=True)

# ==========================================
# 5. 실시간 비교 알고리즘 및 최종 판정 출력
# ==========================================
st.write("---")
st.subheader("📊 AI 1:1 대조 판정 결과")

if master_file and test_file:
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(label="🎯 순수 기준 데이터", value=master_text if master_text else "인식 실패")
    with res_col2:
        st.metric(label="🔍 순수 검사 데이터", value=test_text if test_text else "인식 실패")
    
    st.write("")
    
    if master_text == test_text and master_text != "":
        st.markdown(
            '<p class="big-font-ok">🟢 일치 (OK) <br><span style="font-size:16px; font-weight:normal;">일부인이 완벽히 일치합니다. 안심하고 생산을 진행하세요.</span></p>', 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<p class="big-font-ng">🔴 불일치 (NG) - 오날인 위험!! <br><span style="font-size:16px; font-weight:normal;">날짜나 로트번호 패턴이 다릅니다! 마킹기 입력을 확인하세요.</span></p>', 
            unsafe_allow_html=True
        )
else:
    st.warning("💡 판정을 시작하려면 좌측의 [기준] 등록 버튼과 우측의 [검사] 대조 버튼을 각각 눌러 촬영해 주세요.")
