import streamlit as st
import cv2
import easyocr
import numpy as np
from PIL import Image

# ==========================================
# 1. 페이지 기본 설정 및 디자인 테마 정의
# ==========================================
st.set_page_config(page_title="농심 일부인 오날인 검증 툴", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    .big-font-ok { 
        font-size:32px !important; 
        color: #2ecc71; 
        font-weight: bold; 
        background-color: #e8f8f5; 
        padding: 20px; 
        border-radius: 12px; 
        text-align: center; 
        border: 3px solid #2ecc71; 
    }
    .big-font-ng { 
        font-size:32px !important; 
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
# 2. 상단 헤더 영역 (농심 로고 및 타이틀)
# ==========================================
st.image("nongshim_logo.png", width=180)
st.title("🍜 부산생산1팀 일부인 검증 시스템")
st.caption("작업자 오날인(Mis-printing) 사고 예방을 위한 부산생산1팀 전용 AI 검증 툴")
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
    st.error(f"⚠️ AI 엔진을 불러오는 중 오류가 발생했습니다: {e}")

def extract_text(image):
    if image is None:
        return ""
    img_np = np.array(image)
    result = reader.readtext(img_np, detail=0)
    raw_text = "".join(result).upper()
    cleaned_text = "".join([char for char in raw_text if char.isalnum()])
    return cleaned_text

# ==========================================
# 4. 세션 상태(Session State) 선언 - 촬영 이미지 기억용
# ==========================================
if "master_img_store" not in st.session_state:
    st.session_state.master_img_store = None
if "test_img_store" not in st.session_state:
    st.session_state.test_img_store = None

# ==========================================
# 5. 카메라 단일화 통합 및 모드 선택 (핵심 개선 구역)
# ==========================================
st.subheader("📸 스마트폰 카메라 촬영 및 등록")
mode = st.radio("현재 촬영 목적을 선택하세요", ["🎯 [기준] 마스터 일부인 등록", "🔍 [검사] 매시간 일부인 대조"], horizontal=True)

# 카메라 창을 딱 1개만 띄워 스마트폰 렌즈 충돌 차단
captured_file = st.camera_input("일부인이 화면 정중앙에 수평으로 오도록 조준 후 촬영하세요")

if captured_file:
    # 현재 선택된 모드에 따라 임시 보관함에 찰칵 찍은 사진을 쏙 저장
    if "🎯 [기준]" in mode:
        st.session_state.master_img_store = captured_file
        st.success("🟢 오늘 작업의 '기준 마스터 이미지'가 성공적으로 등록되었습니다! 이제 아래에서 '검사'로 바꾼 뒤 제품을 찍으세요.")
    else:
        st.session_state.test_img_store = captured_file

st.write("---")

# ==========================================
# 6. 현재 등록 상태 모니터링 (두 채널 시각화)
# ==========================================
st.subheader("🖼️ 현재 등록된 이미지 확인")
preview_col1, preview_col2 = st.columns(2)

with preview_col1:
    st.markdown("### 🎯 등록된 [기준] 마스터")
    if st.session_state.master_img_store:
        st.image(st.session_state.master_img_store, use_container_width=True)
    else:
        st.caption("아직 등록된 기준 사진이 없습니다. 위에서 '기준 등록'을 선택하고 촬영해 주세요.")

with preview_col2:
    st.markdown("### 🔍 방금 촬영한 [검사] 대상")
    if st.session_state.test_img_store:
        st.image(st.session_state.test_img_store, use_container_width=True)
    else:
        st.caption("아직 촬영된 검사 사진이 없습니다. 위에서 '일부인 대조'를 선택하고 촬영해 주세요.")

# ==========================================
# 7. 실시간 비교 알고리즘 및 최종 판정 출력
# ==========================================
st.write("---")
st.subheader("📊 AI 1:1 대조 판정 결과")

if st.session_state.master_img_store and st.session_state.test_img_store:
    m_img = Image.open(st.session_state.master_img_store)
    t_img = Image.open(st.session_state.test_img_store)
    
    with st.spinner("AI가 마킹 문자를 정밀 분석하는 중입니다..."):
        master_text = extract_text(m_img)
        test_text = extract_text(t_img)
    
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(label="🎯 기준 데이터", value=master_text if master_text else "인식 실패")
    with res_col2:
        st.metric(label="🔍 검사 데이터", value=test_text if test_text else "인식 실패")
    
    st.write("")
    
    if master_text == test_text and master_text != "":
        st.markdown(
            '<p class="big-font-ok">🟢 일치 (OK) <br><span style="font-size:18px; font-weight:normal;">일부인이 완벽히 일치합니다. 포장 작업을 진행하셔도 좋습니다.</span></p>', 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<p class="big-font-ng">🔴 불일치 (NG) - 오날인 위험!! <br><span style="font-size:18px; font-weight:normal;">유통기한 날짜나 LOT 번호가 다릅니다! 마킹기 입력을 즉시 확인하세요.</span></p>', 
            unsafe_allow_html=True
        )
        if master_text == "" or test_text == "":
            st.warning("⚠️ 사진이 흐리거나 그림자가 지면 AI가 읽지 못합니다. 수평을 맞추고 플래시를 활용해 보세요.")
else:
    st.warning("💡 판정을 시작하려면 상단 카메라를 이용해 [기준] 이미지와 [검사] 이미지를 모두 1번씩 촬영해 주세요.")
