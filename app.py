import streamlit as st
import easyocr
import numpy as np
from PIL import Image, ImageOps
import re
import base64
from io import BytesIO

# 1. 화면 기본 세팅 (모바일 현장 맞춤형 대형 UI)
st.set_page_config(page_title="농심 부산생산1팀 검증 시스템", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #f5f6fa; }
    div.stButton > button {
        width: 100% !important; height: 65px !important;
        font-size: 20px !important; font-weight: bold !important; border-radius: 12px !important;
    }
    .big-font-ok { 
        font-size:32px !important; color: #2ecc71; font-weight: bold; 
        background-color: #e8f8f5; padding: 25px; border-radius: 15px; text-align: center; border: 4px solid #2ecc71; 
    }
    .big-font-ng { 
        font-size:32px !important; color: #e74c3c; font-weight: bold; 
        background-color: #fadbd8; padding: 25px; border-radius: 15px; text-align: center; border: 4px solid #e74c3c; 
    }
    .title-box { font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 5px; }
    .data-text { background-color: #ffffff; padding: 12px; border-radius: 8px; border: 1px solid #cbd5e1; font-family: monospace; font-size: 16px; color: #334155; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 폰 브라우저 캐시 버그를 원천 차단하는 자바스크립트 내장 셔터 컴포넌트
def HTML5_Single_Shutter(key_id, button_text):
    html_code = f"""
    <div style="font-family: sans-serif;">
        <label style="display: block; width: 100%; height: 65px; background-color: #3498db; color: white; 
                      text-align: center; line-height: 65px; font-size: 20px; font-weight: bold; border-radius: 15px; 
                      cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.15);" id="lbl_{key_id}">
            {button_text}
            <input type="file" accept="image/*" capture="environment" id="{key_id}" style="display: none;">
        </label>
        <div id="msg_{key_id}" style="margin-top: 5px; font-size: 14px; color: #7f8c8d; text-align:center;"></div>
    </div>
    <script>
    document.getElementById('lbl_{key_id}').addEventListener('click', function() {{
        document.getElementById('{key_id}').value = "";
    }});
    document.getElementById('{key_id}').addEventListener('change', function(e) {{
        const file = e.target.files[0];
        if (!file) return;
        document.getElementById('msg_{key_id}').innerText = "⚡ 이미지 고강도 압축 중...";
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = function(evt) {{
            const img = new Image();
            img.src = evt.target.result;
            img.onload = function() {{
                const canvas = document.createElement('canvas');
                const maxWidth = 600;
                const scale = maxWidth / img.width;
                canvas.width = maxWidth; canvas.height = img.height * scale;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                const dataUrl = canvas.toDataURL('image/jpeg', 0.4);
                window.parent.postMessage({{type: 'streamlit:setComponentValue', value: dataUrl, key: '{key_id}'}}, '*');
                document.getElementById('msg_{key_id}').innerText = "📸 전송 완료!";
            }}
        }}
    }});
    </script>
    """
    return st.components.v1.html(html_code, height=95)

st.image("nongshim_logo.png", width=140)
st.title("🍜 부산생산1팀 일부인 검증 시스템")
st.caption("초기화 리셋 완료 / 문구+LOT 완벽 매칭 순정 버전 (V15.0)")
st.write("---")

# 2. AI OCR 로딩
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False) 

try:
    reader = load_ocr()
except Exception as e:
    st.error(f"⚠️ AI 엔진 로드 오류: {e}")

def convert_b64_to_pil(base64_str):
    if not base64_str: return None
    try:
        header, encoded = base64_str.split(",", 1)
        return ImageOps.exif_transpose(Image.open(BytesIO(base64.b64decode(encoded))))
    except: return None

# 3. [핵심] 일지 주변 잡글씨를 완벽하게 차단하는 검증 블록 필터링 엔진
def extract_full_marking_block(img_pil):
    if img_pil is None: return ""
    try:
        rotations = [0, 90, 270]
        for angle in rotations:
            test_img = np.array(img_pil if angle == 0 else img_pil.rotate(angle, expand=True))
            result = reader.readtext(test_img, detail=0)
            
            valid_lines = []
            for line in result:
                clean_line = line.upper().strip()
                # 공정일지 속 수많은 노이즈 중 일부인 핵심 단어가 포함된 라인만 조준 타격
                if any(x in clean_line for x in ["MINDESTENS", "HALTBAR", "BIS", "LOT", "TE26"]):
                    valid_lines.append(clean_line)
            
            if valid_lines:
                return " / ".join(valid_lines)
        return "일부인 문구 인식 실패"
    except: return "AI 인식 오류"

# 4. 화면 좌/우 독립형 레이아웃 배치
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="title-box">A. 오늘 작업 기준 마스터 등록</div>', unsafe_allow_html=True)
    master_b64 = HTML5_Single_Shutter("m_shutter", "🎯 기준 마스터 사진 촬영")
    if master_b64:
        st.session_state.final_m_b64 = master_b64
        st.session_state.final_m_txt = extract_full_marking_block(convert_b64_to_pil(master_b64))

    if "final_m_b64" in st.session_state and st.session_state.final_m_b64:
        if "final_m_txt" in st.session_state and st.session_state.final_m_txt:
            st.markdown(f"**🎯 마스터 등록 값:**")
            st.markdown(f'<div class="data-text">{st.session_state.final_m_txt}</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="title-box">B. 매시간 생산 제품 실시간 검사</div>', unsafe_allow_html=True)
    test_b64 = HTML5_Single_Shutter("t_shutter", "🔍 생산 제품 사진 촬영")
    if test_b64:
        st.session_state.final_t_b64 = test_b64
        st.session_state.final_t_txt = extract_full_marking_block(convert_b64_to_pil(test_b64))

    if "final_t_b64" in st.session_state and st.session_state.final_t_b64:
        if "final_t_txt" in st.session_state and st.session_state.final_t_txt:
            st.markdown(f"**🔍 현재 제품 검사 값:**")
            st.markdown(f'<div class="data-text">{st.session_state.final_t_txt}</div>', unsafe_allow_html=True)

# 5. 1:1 최종 대조 판정 구역
st.write("---")
st.subheader("📊 AI 1:1 글자+숫자 완벽 대조 결과")

if "final_m_txt" in st.session_state and "final_t_txt" in st.session_state:
    m_res = st.session_state.final_m_txt
    t_res = st.session_state.final_t_txt
    
    if m_res and t_res and "실패" not in m_res and "실패" not in t_res:
        # 기호나 공백 차이로 인한 NG 오작동 방지 정제작업
        m_compare = m_res.replace(" ", "").replace(":", "").replace("-", "").replace(".", "")
        t_compare = t_res.replace(" ", "").replace(":", "").replace("-", "").replace(".", "")
        
        if m_compare == t_compare:
            st.markdown(f'<p class="big-font-ok">🟢 전체 문구 일치 (OK) <br><span style="font-size:16px; font-weight:normal;">일부인 문구 및 LOT 번호가 마스터와 100% 일치합니다. 생산을 계속 진행하세요.</span></p>', unsafe_allow_html=True)
        else:
            st.markdown(f'<p class="big-font-ng">🔴 문구/LOT 불일치 (NG) <br><span style="font-size:16px; font-weight:normal;">글자나 숫자가 마스터와 다릅니다! 마킹 인쇄 상태를 확인하세요.</span></p>', unsafe_allow_html=True)
else:
    st.info("💡 기준 등록과 제품 촬영을 마치면 상호 대조 판정이 실시간으로 출력됩니다.")

if st.button("🆕 시스템 전체 초기화 (제품 변경 시)"):
    st.session_state.clear()
    st.markdown("""<script>window.parent.location.reload();</script>""", unsafe_allow_html=True)
