import streamlit as st
import cv2
import easyocr
import numpy as np
from PIL import Image, ImageOps
import re

# ==========================================
# 1. 페이지 설정 및 현장용 UI 디자인
# ==========================================
st.set_page_config(page_title="농심 부산생산1팀 일부인 검증", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    .big-font-ok { 
        font-size:28px !important; color: #2ecc71; font-weight: bold; 
        background-color: #e8f8f5; padding: 20px; border-radius: 12px; text-align: center; border: 3px solid #2ecc71; 
    }
    .big-font-ng { 
        font-size:28px !important; color: #e74c3c; font-weight: bold; 
        background-color: #fadbd8; padding: 20px; border-radius: 12px; text-align: center; border: 3px solid #e74c3c; 
        animation: blinker 1.5s linear infinite;
    }
    @keyframes blinker { 50% { opacity: 0.7; } }
    </style>
""", unsafe_allow_html=True)

# 상단 헤더
st.image("nongshim_logo.png", width=150)
st.title("🍜 부산생산1팀 일부인 검증 시스템")
st.caption("실시간 라이브 카메라 및 글자 회전 자동 보정 탑재 버전 (V5.0)")
st.write("---")

# ==========================================
# 2. AI OCR 엔진 초기화
# ==========================================
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False) 

try:
    reader = load_ocr()
except Exception as e:
    st.error(f"⚠️ AI 엔진 로드 오류: {e}")

# [핵심 알고리즘] 누워있는 글자, 점이 찍힌 날짜 패턴을 다각도로 분석하여 추출하는 함수
def extract_nongshim_marking(img_pil):
    if img_pil is None:
        return ""
    
    # 스마트폰 세로 촬영 시 사진이 돌아가는 물리적 현상 방지 (EXIF 방향 보정)
    img_pil = ImageOps.exif_transpose(img_pil)
    
    # AI 인식 속도 향상을 위한 이미지 최적화 리사이징
    if img_pil.width > 800:
        w_percent = (800 / float(img_pil.width))
        h_size = int((float(img_pil.height) * float(w_percent)))
        img_pil = img_pil.resize((800, h_size), Image.Resampling.LANCZOS)
    
    # 원본 및 회전 각도별(0도, 90도, 270도)로 총 3번 정밀 탐색하여 누운 글자 잡아내기
    rotations = [0, 90, 270]
    best_text = ""
    
    for angle in rotations:
        if angle == 0:
            test_img = np.array(img_pil)
        elif angle == 90:
            test_img = np.array(img_pil.rotate(90, expand=True))
        elif angle == 270:
            test_img = np.array(img_pil.rotate(270, expand=True))
            
        result = reader.readtext(test_img, detail=0)
        combined = "".join(result).upper().replace(" ", "")
        
        # 날짜 정규식 패턴 분석 (예: 27.05.2027 또는 20270525 등 패턴 추출)
        # 8자리 숫자 검색 또는 점(.)이 포함된 날짜 양식 검색
        date_match = re.search(r'\d{2}\.\d{2}\.\d{4}|\d{8}', combined)
        
        if date_match:
            date_part = date_match.group(0)
            # 날짜 뒤에 붙은 LOT 번호(예: TE26) 추출
            remaining = combined.replace(date_part, "")
            lot_match = re.search(r'LOT:[A-Z0-9]{2,6}|LOT[A-Z0-9]{2,6}|[A-Z]{2}\d{2}', remaining)
            lot_part = lot_match.group(0) if lot_match else ""
            
            # 깔끔하게 필터링된 결과 조립 및 반환
            return f"📅{date_part} / 📦{lot_part}".strip()
            
        if len(combined) > len(best_text):
            best_text = combined
            
    return best_text # 만약 규격 날짜 패턴 실패 시 가장 길게 읽은 텍스트 반환

# ==========================================
# 3. 실시간 라이브 카메라 UI (가장 직관적인 투트랙)
# ==========================================
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🎯 1단계: [기준] 마스터 등록")
    # 화면에서 즉시 켜지는 안정적인 스트림릿 네이티브 실시간 웹캠 창
    master_cam = st.camera_input("기준 오더지 또는 초물 제품을 정면으로 조준해 찍으세요", key="cam_master")
    
    master_text = ""
    if master_cam:
        m_img = Image.open(master_cam)
        with st.spinner("AI가 기준 마킹 분석 중..."):
            master_text = extract_nongshim_marking(m_img)
        st.success(f"🎯 기준 분석 완료: {master_text}")

with col2:
    st.markdown("### 🔍 2단계: [검사] 매시간 대조")
    test_cam = st.camera_input("현재 라인에서 나온 검사 대상 제품을 찍으세요", key="cam_test")
    
    test_text = ""
    if test_cam:
        t_img = Image.open(test_cam)
        with st.spinner("AI가 검사 대상 분석 중..."):
            test_text = extract_nongshim_marking(t_img)
        st.success(f"🔍 검사 분석 완료: {test_text}")

# ==========================================
# 4. 최종 1:1 대조 판정 결과 출력
# ==========================================
st.write("---")
st.subheader("📊 AI 1:1 대조 판정 결과")

if master_cam and test_cam:
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(label="🎯 순수 기준 데이터", value=master_text if master_text else "인식 실패")
    with res_col2:
        st.metric(label="🔍 순수 검사 데이터", value=test_text if test_text else "인식 실패")
    
    st.write("")
    
    # 알맹이 데이터가 완벽히 일치하는지 비교
    if master_text == test_text and master_text != "":
        st.markdown(
            '<p class="big-font-ok">🟢 일치 (OK) <br><span style="font-size:16px; font-weight:normal;">일부인이 완벽히 일치합니다. 안심하고 생산을 진행하세요.</span></p>', 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<p class="big-font-ng">🔴 불일치 (NG) - 오날인 위험!! <br><span style="font-size:16px; font-weight:normal;">날짜나 로트번호가 다릅니다! 마킹기 출력을 즉시 확인하세요.</span></p>', 
            unsafe_allow_html=True
        )
else:
    st.warning("💡 판정을 시작하려면 좌측의 [기준] 카메라와 우측의 [검사] 카메라로 각각 'Take Photo'를 눌러 촬영해 주세요.")
