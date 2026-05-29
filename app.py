import streamlit as st
import cv2
import easyocr
import numpy as np
from PIL import Image, ImageOps
import re

# ==========================================
# 1. 모바일 풀-스크린 카메라 뷰 및 대형 UI 강제 주입
# ==========================================
st.set_page_config(page_title="농심 부산생산1팀 검증 시스템", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    
    /* [핵심] 답답한 4:3 웹캠 상자를 모바일 화면에 맞춰 대폭 확대 */
    [data-testid="stCameraInput"] > div {
        width: 100% !important;
        max-width: 500px !important;
        margin: 0 auto !important;
    }
    
    /* 내부 비디오 라이브 스트리밍 화면 크기를 세로로 길게 늘려 시인성 확보 */
    [data-testid="stCameraInput"] video {
        width: 100% !important;
        height: auto !important;
        transform: scale(1.2); /* 화면을 120% 강제 확대하여 큼직하게 보이게 함 */
        border-radius: 12px;
    }
    
    /* Take Photo 촬영 버튼을 장갑 끼고도 누르기 쉽게 대형화 */
    [data-testid="stCameraInput"] button {
        height: 50px !important;
        font-size: 18px !important;
        background-color: #2c3e50 !important;
        color: white !important;
        border-radius: 8px !important;
        margin-top: 10px !important;
    }
    
    /* 현장용 액션 등록 버튼 스타일 */
    div.stButton > button {
        width: 100% !important;
        height: 55px !important;
        font-size: 18px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
    }
    .big-font-ok { 
        font-size:26px !important; color: #2ecc71; font-weight: bold; 
        background-color: #e8f8f5; padding: 15px; border-radius: 12px; text-align: center; border: 3px solid #2ecc71; 
    }
    .big-font-ng { 
        font-size:26px !important; color: #e74c3c; font-weight: bold; 
        background-color: #fadbd8; padding: 15px; border-radius: 12px; text-align: center; border: 3px solid #e74c3c; 
    }
    </style>
""", unsafe_allow_html=True)

# 상단 타이틀
st.image("nongshim_logo.png", width=130)
st.title("🍜 부산생산1팀 일부인 검증 시스템")
st.caption("모바일 꽉 찬 화면 줌-인 카메라 적용 버전 (V6.1)")
st.write("---")

# ==========================================
# 2. AI OCR 엔진 및 텍스트 정제 알고리즘
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
    if img_pil.width > 800:
        w_percent = (800 / float(img_pil.width))
        h_size = int((float(img_pil.height) * float(w_percent)))
        img_pil = img_pil.resize((800, h_size), Image.Resampling.LANCZOS)
    
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
# 3. 데이터 보관용 가상 메모리(Session State) 세팅
# ==========================================
if "stored_master_img" not in st.session_state:
    st.session_state.stored_master_img = None
if "stored_master_text" not in st.session_state:
    st.session_state.stored_master_text = ""
if "stored_test_img" not in st.session_state:
    st.session_state.stored_test_img = None
if "stored_test_text" not in st.session_state:
    st.session_state.stored_test_text = ""

# ==========================================
# 4. [상단] 단일 통합 실시간 카메라 배치
# ==========================================
st.subheader("📸 현장 실시간 카메라 촬영")

# 스타일 주입으로 이제 이전보다 훨씬 큼직하게 보입니다.
live_photo = st.camera_input("일부인이 선명하게 보이도록 조준 후 아래 'Take Photo'를 누르세요")

if live_photo:
    st.write("👇 방금 찍은 사진을 어디로 등록할지 선택하세요:")
    save_col1, save_col2 = st.columns(2)
    
    with save_col1:
        if st.button("🎯 오늘 작업 [기준 마스터]로 등록하기", key="btn_save_master"):
            st.session_state.stored_master_img = live_photo
            pil_img = Image.open(live_photo)
            st.session_state.stored_master_text = extract_nongshim_marking(pil_img)
            st.success("🟢 기준 마스터 등록 완료!")
            
    with save_col2:
        if st.button("🔍 매시간 [검사 대상]으로 대조하기", key="btn_save_test"):
            st.session_state.stored_test_img = live_photo
            pil_img = Image.open(live_photo)
            st.session_state.stored_test_text = extract_nongshim_marking(pil_img)
            st.success("🟢 검사 대상 대조 완료!")

st.write("---")

# ==========================================
# 5. [하단] 현재 저장된 데이터 모니터링 모듈
# ==========================================
st.subheader("🖼️ 실시간 공정 라인 모니터링")
view_col1, view_col2 = st.columns(2)

with view_col1:
    st.markdown("#### 🎯 등록된 [기준] 데이터")
    if st.session_state.stored_master_img:
        st.image(st.session_state.stored_master_img, use_container_width=True)
        st.code(st.session_state.stored_master_text)
    else:
        st.caption("등록된 기준 사진이 없습니다.")

with view_col2:
    st.markdown("#### 🔍 현재 [검사] 데이터")
    if st.session_state.stored_test_img:
        st.image(st.session_state.stored_test_img, use_container_width=True)
        st.code(st.session_state.stored_test_text)
    else:
        st.caption("촬영된 검사 사진이 없습니다.")

# ==========================================
# 6. 최종 판정 디스플레이
# ==========================================
st.write("---")
st.subheader("📊 AI 1:1 대조 판정 결과")

m_txt = st.session_state.stored_master_text
t_txt = st.session_state.stored_test_text

if m_txt and t_txt:
    if m_txt == t_txt:
        st.markdown(
            f'<p class="big-font-ok">🟢 일치 (OK) <br><span style="font-size:16px; font-weight:normal;">일부인이 완벽히 일치합니다. ({m_txt})</span></p>', 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<p class="big-font-ng">🔴 불일치 (NG) - 오날인 위험!! <br><span style="font-size:16px; font-weight:normal;">마킹이 다릅니다! <br>기준: {m_txt} / 검사: {t_txt}</span></p>', 
            unsafe_allow_html=True
        )
else:
    st.warning("💡 상단 카메라로 사진을 찍어 [기준 등록]과 [검사 대조]를 각각 진행하면 실시간 판정이 시작됩니다.")
