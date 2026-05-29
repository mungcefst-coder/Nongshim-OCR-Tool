import streamlit as st
import cv2
import easyocr
import numpy as np
from PIL import Image, ImageOps
import re

# ==========================================
# 1. 페이지 설정 및 모바일 대형 UI 스타일
# ==========================================
st.set_page_config(page_title="농심 부산생산1팀 검증 시스템", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    
    /* 현장용 대형 스마트폰 버튼 커스텀 */
    div.stButton > button {
        width: 100% !important;
        height: 70px !important;
        font-size: 22px !important;
        font-weight: bold !important;
        border-radius: 15px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
    }
    
    section[data-testid="stFileUploader"] {
        padding: 10px 0;
    }
    section[data-testid="stFileUploader"] label {
        font-size: 20px !important;
        font-weight: bold !important;
        color: #2c3e50 !important;
    }
    
    .status-box {
        padding: 15px;
        border-radius: 10px;
        background-color: #ebf5fb;
        border-left: 5px solid #3498db;
        margin-bottom: 20px;
        font-size: 18px;
        font-weight: bold;
    }
    
    .big-font-ok { 
        font-size:32px !important; color: #2ecc71; font-weight: bold; 
        background-color: #e8f8f5; padding: 25px; border-radius: 15px; text-align: center; border: 4px solid #2ecc71; 
    }
    .big-font-ng { 
        font-size:32px !important; color: #e74c3c; font-weight: bold; 
        background-color: #fadbd8; padding: 25px; border-radius: 15px; text-align: center; border: 4px solid #e74c3c; 
    }
    </style>
""", unsafe_allow_html=True)

# 상단 타이틀
st.image("nongshim_logo.png", width=140)
st.title("🍜 부산생산1팀 일부인 검증 시스템")
st.caption("모바일 브라우저 튕김 방지용 경량 압축 파이프라인 탑재 버전 (V7.1)")
st.write("---")

# ==========================================
# 2. AI OCR 엔진 및 정밀 패턴 필터
# ==========================================
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False) 

try:
    reader = load_ocr()
except Exception as e:
    st.error(f"⚠️ AI 엔진 로드 오류: {e}")

def extract_nongshim_marking(img_pil):
    if img_pil is None:
        return ""
    
    img_pil = ImageOps.exif_transpose(img_pil)
    
    # 폰이 기적적으로 버텨서 올린 이미지를 서버 받자마자 즉시 600px로 쪼개기
    if img_pil.width > 600:
        w_percent = (600 / float(img_pil.width))
        h_size = int((float(img_pil.height) * float(w_percent)))
        img_pil = img_pil.resize((600, h_size), Image.Resampling.LANCZOS)
    
    rotations = [0, 90, 270]
    for angle in rotations:
        test_img = np.array(img_pil if angle == 0 else img_pil.rotate(angle, expand=True))
        result = reader.readtext(test_img, detail=0)
        combined = "".join(result).upper().replace(" ", "")
        
        date_match = re.search(r'\d{2}\.\d{2}\.\d{4}|\d{8}', combined)
        if date_match:
            date_part = date_match.group(0)
            remaining = combined.replace(date_part, "")
            lot_match = re.search(r'LOT:[A-Z0-9]{2,6}|LOT[A-Z0-9]{2,6}|[A-Z]{2}\d{2}', remaining)
            lot_part = lot_match.group(0) if lot_match else ""
            return f"📅 {date_part} / 📦 {lot_part}".strip()
            
    return combined

# ==========================================
# 3. 시스템 단계 제어용 메모리 세팅
# ==========================================
if "step" not in st.session_state:
    st.session_state.step = "MASTER_WAIT"  
if "master_txt" not in st.session_state:
    st.session_state.master_txt = ""
if "master_img" not in st.session_state:
    st.session_state.master_img = None
if "test_txt" not in st.session_state:
    st.session_state.test_txt = ""
if "test_img" not in st.session_state:
    st.session_state.test_img = None

# ==========================================
# 4. 단계별 내비게이션 및 카메라 트리거
# ==========================================

# [1단계] 기준 마스터 촬영 대기 상태
if st.session_state.step == "MASTER_WAIT":
    st.markdown('<div class="status-box">📢 [안내] 오늘 작업할 기준 마스터(표준 샘플)를 촬영해 주세요.</div>', unsafe_allow_html=True)
    
    # [핵심 변경] 용량이 큰 무손실 png를 원천 차단하고 오직 경량화된 jpeg만 받도록 선언하여 스마트폰의 자체 압축 유도
    master_file = st.file_uploader("🎯 여기에 터치하여 [기준 마스터] 촬영", type=["jpg", "jpeg"], key="cam_master_raw")
    
    if master_file:
        m_img = Image.open(master_file)
        with st.spinner("AI가 기준 마킹 분석 중..."):
            st.session_state.master_txt = extract_nongshim_marking(m_img)
        st.session_state.master_img = master_file
        st.session_state.step = "TEST_WAIT" 
        st.rerun()

# [2단계] 생산 제품 대조 촬영 대기 상태
elif st.session_state.step == "TEST_WAIT":
    st.markdown('<div class="status-box">📢 [안내] 기준 등록 완료! 이제 현재 라인에서 생산된 제품을 촬영해 주세요.</div>', unsafe_allow_html=True)
    
    # 여기도 오직 jpeg 포맷만 받도록 제한하여 브라우저의 튕김 메모리 마진 확보
    test_file = st.file_uploader("🔍 여기에 터치하여 [생산 제품] 촬영", type=["jpg", "jpeg"], key="cam_test_raw")
    
    if test_file:
        t_img = Image.open(test_file)
        with st.spinner("AI가 생산 마킹 분석 중..."):
            st.session_state.test_txt = extract_nongshim_marking(t_img)
        st.session_state.test_img = test_file
        st.session_state.step = "RESULT" 
        st.rerun()

# [3단계] 최종 판정 결과 확인 및 다음 액션 유도
elif st.session_state.step == "RESULT":
    st.subheader("📊 AI 1:1 대조 판정 결과")
    
    m_txt = st.session_state.master_txt
    t_txt = st.session_state.test_txt
    
    if m_txt == t_txt and m_txt != "":
        st.markdown(
            f'<p class="big-font-ok">🟢 일치 (OK) <br><span style="font-size:18px; font-weight:normal;">일부인이 완벽히 일치합니다. 생산을 계속 진행하세요.<br>({m_txt})</span></p>', 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<p class="big-font-ng">🔴 불일치 (NG) - 오날인 위험!! <br><span style="font-size:18px; font-weight:normal;">날짜나 로트번호가 다릅니다!<br>🎯 기준: {m_txt if m_txt else "인식 실패"}<br>🔍 검사: {t_txt if t_txt else "인식 실패"}</span></p>', 
            unsafe_allow_html=True
        )
        
    st.write("---")
    
    col_img1, col_img2 = st.columns(2)
    with col_img1:
        st.image(st.session_state.master_img, caption=f"🎯 세팅된 기준: {m_txt}", use_container_width=True)
    with col_img2:
        st.image(st.session_state.test_img, caption=f"🔍 방금 검사한 제품: {t_txt}", use_container_width=True)
        
    st.write("---")
    
    act_col1, act_col2 = st.columns(2)
    with act_col1:
        if st.button("🔄 다음 생산제품 추가 검사 (매시간 검사)", key="next_test"):
            st.session_state.test_img = None
            st.session_state.test_txt = ""
            st.session_state.step = "TEST_WAIT" 
            st.rerun()
            
    with act_col2:
        if st.button("🆕 완전히 새로운 기준 등록 (교대조/제품변경)", key="reset_all"):
            st.session_state.clear() 
            st.rerun()
