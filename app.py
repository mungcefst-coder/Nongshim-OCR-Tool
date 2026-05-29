import streamlit as st
import cv2
import easyocr
import numpy as np
from PIL import Image, ImageOps
import re
import base64
from io import BytesIO

# ==========================================
# 1. 페이지 기본 설정 및 모바일 대형 UI 스타일
# ==========================================
st.set_page_config(page_title="농심 부산생산1팀 검증 시스템", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    .status-box {
        padding: 15px; border-radius: 10px; background-color: #ebf5fb;
        border-left: 5px solid #3498db; margin-bottom: 20px; font-size: 18px; font-weight: bold;
    }
    .big-font-ok { 
        font-size:32px !important; color: #2ecc71; font-weight: bold; 
        background-color: #e8f8f5; padding: 25px; border-radius: 15px; text-align: center; border: 4px solid #2ecc71; 
    }
    .big-font-ng { 
        font-size:32px !important; color: #e74c3c; font-weight: bold; 
        background-color: #fadbd8; padding: 25px; border-radius: 15px; text-align: center; border: 4px solid #e74c3c; 
    }
    div.stButton > button {
        width: 100% !important;
        height: 65px !important;
        font-size: 20px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
    }
    </style>
""", unsafe_allow_html=True)

# [핵심 기술] 전송 후 스스로를 파괴하여 데이터 고임을 원천 차단하는 울트라 압축 컴포넌트
def HTML5_Super_Compressor(key_id, button_text):
    html_code = f"""
    <div style="font-family: sans-serif;">
        <label style="display: block; width: 100%; height: 65px; background-color: #3498db; color: white; 
                      text-align: center; line-height: 65px; font-size: 20px; font-weight: bold; border-radius: 15px; 
                      cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.15);">
            {button_text}
            <input type="file" accept="image/*" capture="environment" id="{key_id}" style="display: none;">
        </label>
        <div id="msg_{key_id}" style="margin-top: 5px; font-size: 14px; color: #7f8c8d; text-align:center;"></div>
    </div>
    <script>
    document.getElementById('{key_id}').addEventListener('change', function(e) {{
        const file = e.target.files[0];
        if (!file) return;
        document.getElementById('msg_{key_id}').innerText = "⚡ 포장재 이미지 고강도 압축 중...";
        
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = function(evt) {{
            const img = new Image();
            img.src = evt.target.result;
            img.onload = function() {{
                const canvas = document.createElement('canvas');
                const maxWidth = 500;
                const scale = maxWidth / img.width;
                canvas.width = maxWidth;
                canvas.height = img.height * scale;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                
                // 화질 30% 압축으로 수십 KB짜리 초경량화
                const dataUrl = canvas.toDataURL('image/jpeg', 0.3);
                
                // [무한루프 방지 구역] 데이터를 보내고 나서 폰이 이 값을 붙잡지 못하도록 즉시 초기화 장치 가동
                window.parent.postMessage({{type: 'streamlit:setComponentValue', value: dataUrl, key: '{key_id}'}}, '*');
                document.getElementById('msg_{key_id}').innerText = "📸 전송 완료!";
                
                // 대기 통로 청소
                setTimeout(function() {{
                    document.getElementById('{key_id}').value = "";
                }}, 100);
            }}
        }}
    }});
    </script>
    """
    return st.components.v1.html(html_code, height=95)

# 타이틀
st.image("nongshim_logo.png", width=140)
st.title("🍜 부산생산1팀 일부인 검증 시스템")
st.caption("전송 통로 자동 파괴 및 휘발성 메모리 리셋 적용 버전 (V9.5 - 최종 완결판)")
st.write("---")

# ==========================================
# 2. 고성능 파이썬 AI OCR 엔진 및 전방위 탐색 알고리즘
# ==========================================
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False) 

try:
    reader = load_ocr()
except Exception as e:
    st.error(f"⚠️ AI 엔진 로드 오류: {e}")

def convert_b64_to_pil(base64_str):
    if not base64_str:
        return None
    try:
        header, encoded = base64_str.split(",", 1)
        data = base64.b64decode(encoded)
        img_pil = Image.open(BytesIO(data))
        return ImageOps.exif_transpose(img_pil)
    except:
        return None

def extract_high_perf_marking(img_pil):
    if img_pil is None:
        return "이미지 분석 불가"
    try:
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
        return combined if "".join(result).strip() else "날짜 인식 실패"
    except:
        return "AI 인식 오류 발생"

# ==========================================
# 3. 세션 메모리 초기화 공장 세팅
# ==========================================
if "step" not in st.session_state:
    st.session_state.step = "STAGE_1"
if "m_b64" not in st.session_state:
    st.session_state.m_b64 = None
if "m_txt" not in st.session_state:
    st.session_state.m_txt = ""
if "t_b64" not in st.session_state:
    st.session_state.t_b64 = None
if "t_txt" not in st.session_state:
    st.session_state.t_txt = ""

# ==========================================
# 4. 단방향 완벽 제어 UI 시퀀스
# ==========================================

# [1단계] 기준 샘플 촬영
if st.session_state.step == "STAGE_1":
    st.markdown('<div class="status-box">📢 [1단계] 오늘 작업할 기준 마스터(표준 샘플)를 촬영해 주세요.</div>', unsafe_allow_html=True)
    m_res = HTML5_Super_Compressor("m_comp", "🎯 기준 마스터 사진 촬영")
    
    if m_res:
        st.session_state.m_b64 = m_res
        pil_img = convert_b64_to_pil(m_res)
        st.session_state.m_txt = extract_high_perf_marking(pil_img)
        st.session_state.step = "STAGE_2"
        st.rerun()

# [2단계] 생산 제품 촬영
elif st.session_state.step == "STAGE_2":
    st.markdown('<div class="status-box">📢 [2단계] 기준 등록 완료! 현재 라인의 생산 제품을 촬영해 주세요.</div>', unsafe_allow_html=True)
    t_res = HTML5_Super_Compressor("t_comp", "🔍 생산 제품 사진 촬영")
    
    if t_res:
        st.session_state.t_b64 = t_res
        pil_img = convert_b64_to_pil(t_res)
        st.session_state.t_txt = extract_high_perf_marking(pil_img)
        st.session_state.step = "STAGE_3"
        st.rerun()

# [3단계] 결과 확인 및 강제 휘발성 청소
elif st.session_state.step == "STAGE_3":
    st.subheader("📊 AI 1:1 대조 판정 결과")
    
    m_txt = st.session_state.m_txt
    t_txt = st.session_state.t_txt
    
    if m_txt == t_txt and "실패" not in m_txt and m_txt != "":
        st.markdown(
            f'<p class="big-font-ok">🟢 일치 (OK) <br><span style="font-size:16px; font-weight:normal;">일부인이 완벽히 일치합니다. 생산을 계속 진행하세요.<br>({m_txt})</span></p>', 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<p class="big-font-ng">🔴 불일치 (NG) - 오날인 위험!! <br><span style="font-size:16px; font-weight:normal;">마킹 정보가 일치하지 않습니다!<br>🎯 기준 세팅: {m_txt}<br>🔍 실시간 검사: {t_txt}</span></p>', 
            unsafe_allow_html=True
        )
        
    st.write("---")
    img_col1, img_col2 = st.columns(2)
    with img_col1:
        m_pil = convert_b64_to_pil(st.session_state.m_b64)
        if m_pil: st.image(m_pil, caption="🎯 등록된 기준 마스터", use_container_width=True)
    with img_col2:
        t_pil = convert_b64_to_pil(st.session_state.t_b64)
        if t_pil: st.image(t_pil, caption="🔍 방금 검사한 생산 제품", use_container_width=True)

    st.write("---")
    
    # [최종 열쇠] 버튼 클릭 시, 이전 데이터의 흔적을 서버와 브라우저 양쪽에서 폭파시킵니다.
    act_col1, act_col2 = st.columns(2)
    with act_col1:
        if st.button("🔄 다음 생산제품 추가 검사 (매시간 검사)", key="btn_clear_test"):
            st.session_state.t_b64 = None
            st.session_state.t_txt = ""
            st.session_state.step = "STAGE_2" # 2단계로 부드럽게 복귀
            st.rerun()
            
    with act_col2:
        if st.button("🆕 완전히 새로운 기준 등록", key="btn_clear_all"):
            st.session_state.clear() # 완전히 초기화
            st.session_state.step = "STAGE_1"
            st.rerun()
