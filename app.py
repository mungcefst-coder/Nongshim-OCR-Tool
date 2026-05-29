import streamlit as st
import cv2
import easyocr
import numpy as np
from PIL import Image, ImageOps
import re

# ==========================================
# 1. 모바일 최적화 대형 UI 및 카메라 뷰어 커스텀
# ==========================================
st.set_page_config(page_title="농심 부산생산1팀 검증 시스템", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    /* 카메라 입력창을 모바일 가로폭에 꽉 차게 확대 */
    [data-testid="stCameraInput"] {
        width: 100% !important;
        max-width: 600px !important;
        margin: 0 auto !important;
    }
    /* 현장용 대형 액션 버튼 스타일 */
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
st.caption("모바일 풀-스크린 카메라 및 에러 원천 차단 버전 (V6.0)")
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
    
    # 90도씩 돌려가며 3방향 정밀 스캔 (세로 촬영 대응)
    rotations = [0, 90, 270]
    for angle in rotations:
        test_img = np.array(img_pil if angle == 0 else img_pil.rotate(angle, expand=True))
        result = reader.readtext(test_img, detail=0)
        combined = "".join(result).upper().replace(" ", "")
        
        # 날짜 포맷 추출 (. 점 포함 패턴 대응)
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
# 4. [상단] 단일 통합 실시간 카메라 배치 (핵심 변혁 구역)
# ==========================================
st.subheader("📸 현장 실시간 카메라 촬영")
st.info("💡 렌즈 충돌을 막기 위해 카메라를 하나로 통합했습니다. 반전 버튼을 자유롭게 사용하세요!")

# 화면에 단 한 개만 존재하는 큼직한 실시간 카메라 창
live_photo = st.camera_input("일부인이 선명하게 보이도록 조준 후 아래 'Take Photo'를 누르세요")

# 사진이 촬영되었을 때만 어디에 저장할지 선택하는 큼직한 버튼 등장
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
            f'<p class="big-font-ok">🟢 일치 (OK) <br><span style="font-size:16px; font-weight:normal;">일부인이 정상입니다. ({m_txt})</span></p>', 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<p class="big-font-ng">🔴 불일치 (NG) - 오날인 위험!! <br><span style="font-size:16px; font-weight:normal;">마킹이 다릅니다! <br>기준: {m_txt} / 검사: {t_txt}</span></p>', 
            unsafe_allow_html=True
        )
else:
    st.warning("💡 상단 카메라로 사진을 찍어 [기준 등록]과 [검사 대조]를 각각 진행하면 실시간 판정이 시작됩니다.")
