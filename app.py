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

# [프론트엔드 핵심] 사진 전송 즉시 0.1초 만에 용량을 압축하여 전송하는 특제 컴포넌트
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
                const dataUrl = canvas.toDataURL('image/jpeg', 0.3);
                window.parent.postMessage({{type: 'streamlit:setComponentValue', value: dataUrl, key: '{key_id}'}}, '*');
                document.getElementById('msg_{key_id}').innerText = "📸 전송 완료!";
            }}
        }}
    }});
    </script>
    """
    return st.components.v1.html(html_code, height=95)

# 타이틀
st.image("nongshim_logo.png", width=140)
st.title("🍜 부산생산1팀 일부인 검증 시스템")
st.caption("스마트폰 브라우저 캐시 강제 무력화 버전 (V9.4 - 무한루프 완전 종결)")
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
# 3. [완전 개조] 화면 오작동 우회용 메모리 트리
# ==========================================
if "m_b64_data" not in st.session_state:
    st.session_state.m_b64_data = None
if "m_text_data" not in st.session_state:
    st.session_state.m_text_data = ""

# ==========================================
# 4. 물 흐르듯 흐르는 단방향 UI 배치
# ==========================================

# [1단계] 기준 마스터 촬영 (기준이 없을 때만 보임)
if st.session_state.m_b64_data is None:
    st.markdown('<div class="status-box">📢 [1단계] 오늘 작업할 기준 마스터(표준 샘플)를 촬영해 주세요.</div>', unsafe_allow_html=True)
    master_res = HTML5_Super_Compressor("m_engine", "🎯 기준 마스터 사진 촬영")
    
    if master_res:
        st.session_state.m_b64_data = master_res
        pil_img = convert_b64_to_pil(master_res)
        st.session_state.m_text_data = extract_high_perf_marking(pil_img)
        st.rerun()

# [2단계] 기준 등록이 완료되면 검사 촬영 및 결과가 한 화면에 즉시 순차 표출
else:
    st.markdown('<div class="status-box">📢 [2단계] 기준 마스터가 등록되었습니다. 이제 생산 제품을 촬영해 주세요.</div>', unsafe_allow_html=True)
    
    # 1단계와 2단계의 구역을 완벽히 분리하여 꼬임 방지
    test_res = HTML5_Super_Compressor("t_engine_final", "🔍 생산 제품 사진 촬영")
    
    # 생산 제품 사진이 들어오는 순간 아래에 판정 결과를 실시간으로 즉시 출력
    if test_res:
        st.write("---")
        st.subheader("📊 AI 1:1 대조 판정 결과")
        
        t_pil = convert_b64_to_pil(test_res)
        test_text_data = extract_high_perf_marking(t_pil)
        master_text_data = st.session_state.m_text_data
        
        if master_text_data == test_text_data and "실패" not in master_text_data and master_text_data != "":
            st.markdown(
                f'<p class="big-font-ok">🟢 일치 (OK) <br><span style="font-size:16px; font-weight:normal;">일부인이 완벽히 일치합니다. 생산을 계속 진행하세요.<br>({master_text_data})</span></p>', 
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<p class="big-font-ng">🔴 불일치 (NG) - 오날인 위험!! <br><span style="font-size:16px; font-weight:normal;">마킹 정보가 일치하지 않습니다!<br>🎯 기준 세팅: {master_text_data}<br>🔍 실시간 검사: {test_text_data}</span></p>', 
                unsafe_allow_html=True
            )
            
        st.write("---")
        img_col1, img_col2 = st.columns(2)
        with img_col1:
            m_pil = convert_b64_to_pil(st.session_state.m_b64_data)
            if m_pil:
                st.image(m_pil, caption=f"🎯 등록된 기준 마스터 마킹", use_container_width=True)
        with img_col2:
            if t_pil:
                st.image(t_pil, caption=f"🔍 방금 검사한 생산 제품 마킹", use_container_width=True)

    st.write("---")
    
    # [핵심 돌파구] 자바스크립트를 이용해 웹브라우저 자체를 셧다운 후 새로고침하여 찌꺼기를 완전히 증발시킴
    if st.button("🔄 다음 생산제품 추가 검사 (매시간 검사 / 화면 리셋)", key="btn_final_refresh"):
        st.markdown("""
            <script>
            window.parent.location.reload();
            </script>
        """, unsafe_allow_html=True)
        st.session_state.clear()
        st.stop()
