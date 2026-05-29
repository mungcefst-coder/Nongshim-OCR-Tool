import streamlit as st
import cv2
import easyocr
import numpy as np
from PIL import Image

# ==========================================
# 1. 페이지 기본 설정 및 디자인 테마 정의
# ==========================================
st.set_page_config(page_title="농심 일부인 오날인 검증 툴", layout="wide")

# 현장 맞춤형 UI 스타일 (글자 크기 키우고, 가시성 극대화)
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
# 위키미디어의 공식 농심 로고 벡터 이미지를 활용합니다.
st.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/Nongshim_Logo.svg/1280px-Nongshim_Logo.svg.png", 
    width=180
)
st.title("🍜 수출전문공장 일부인 1:1 비교 검증 시스템")
st.caption("공장 현장 작업자 오날인(Mis-printing) 에러 방지용 단독형 AI 프로토타입")
st.write("---")

# ==========================================
# 3. AI OCR 엔진 초기화 (최초 1회만 실행)
# ==========================================
@st.cache_resource
def load_ocr():
    # CPU 기반 구동으로 클라우드 서버 환경 최적화
    return easyocr.Reader(['en'], gpu=False) 

try:
    reader = load_ocr()
except Exception as e:
    st.error(f"⚠️ AI 엔진을 불러오는 중 오류가 발생했습니다: {e}")

# ==========================================
# 4. 이미지 텍스트 추출 및 전처리 알고리즘
# ==========================================
def extract_text(image):
    if image is None:
        return ""
    
    # PIL 이미지 포맷을 OpenCV/Numpy 배열로 변환
    img_np = np.array(image)
    
    # AI OCR 글자 판독 실행
    result = reader.readtext(img_np, detail=0)
    
    # 알파벳과 숫자만 추출 (오진을 유발하는 띄어쓰기, 마침표, 콜론 등 특수문자 완벽 제거)
    raw_text = "".join(result).upper()
    cleaned_text = "".join([char for char in raw_text if char.isalnum()])
    return cleaned_text

# ==========================================
# 5. 2단 작업 화면 구성 (좌측: 기준 마스터 / 우측: 실시간 검사)
# ==========================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("1단계: [기준] 마스터 일부인 등록")
    st.info("오늘 작업할 올바른 '오더지' 또는 첫 번째 '정상 제품(초물)'의 일부인을 촬영하세요.")
    
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
    st.info("현재 라인에서 포장되어 나온 제품의 일부인을 오려서 카메라로 찍으세요.")
    
    test_source = st.radio("검사 이미지 입력 방식", ["카메라 촬영", "파일 업로드"], key="test_src")
    test_img = None
    
    if test_source == "카메라 촬영":
        test_img = st.camera_input("현재 제품 일부인 촬영", key="cam_test")
    else:
        test_img = st.file_uploader("검사 이미지 파일 선택", type=["jpg", "jpeg", "png"], key="file_test")
        if test_img:
            st.image(test_img, caption="방금 촬영된 검사 대상", use_container_width=True)

# ==========================================
# 6. 실시간 비교 알고리즘 및 최종 판정 출력
# ==========================================
st.write("---")
st.subheader("3단계: AI 1:1 대조 판정 결과")

if master_img and test_img:
    # 업로드된 이미지 파일 열기
    m_img = Image.open(master_img)
    t_img = Image.open(test_img)
    
    # 로딩 애니메이션 구현
    with st.spinner("AI가 마킹 문자를 정밀 분석하는 중입니다..."):
        master_text = extract_text(m_img)
        test_text = extract_text(t_img)
    
    # 판독된 데이터 매칭 상태 시각화
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(label="🎯 기준 데이터 (공백/특수문자 제외)", value=master_text if master_text else "인식 실패")
    with res_col2:
        st.metric(label="🔍 검사 데이터 (공백/특수문자 제외)", value=test_text if test_text else "인식 실패")
    
    st.write("")
    
    # 최종 문자열 1:1 완전 대조 판정
    if master_text == test_text and master_text != "":
        st.markdown(
            '<p class="big-font-ok">🟢 일치 (OK) <br><span style="font-size:18px; font-weight:normal;">일부인이 정상입니다. 포장 작업을 계속 진행하셔도 좋습니다.</span></p>', 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<p class="big-font-ng">🔴 불일치 (NG) - 오날인 위험!! <br><span style="font-size:18px; font-weight:normal;">유통기한 날짜나 LOT 번호가 다릅니다! 마킹기 입력을 즉시 확인하세요.</span></p>', 
            unsafe_allow_html=True
        )
        if master_text == "" or test_text == "":
            st.warning("⚠️ 사진의 초점이 흐리거나 조명이 어두우면 AI가 글자를 읽지 못합니다. 가이드라인 거치대에 맞추어 다시 촬영해 보세요.")
else:
    st.warning("💡 판정을 시작하려면 좌측의 [기준] 이미지와 우측의 [검사] 이미지를 모두 등록(촬영)해 주세요.")
