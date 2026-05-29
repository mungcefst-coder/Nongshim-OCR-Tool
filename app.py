import streamlit as st
import cv2
import easyocr
import numpy as np
from PIL import Image
import re
import base64
from io import BytesIO

# ==========================================
# 1. 페이지 설정 및 실시간 모바일 압축 자바스크립트 내장
# ==========================================
st.set_page_config(page_title="농심 일부인 검증 시스템", layout="wide")

# [핵심 기술] 스마트폰 카메라가 사진을 찍자마자 브라우저 메모리 안에서 가로 600px로 초고속 압축하여 
# 서버로 전송하는 HTML5/JavaScript 컴포넌트입니다. (메모리 폭발 방지)
def HTML5_Camera_Compressor(key_id, button_text):
    html_code = f"""
    <div style="font-family: sans-serif; margin-bottom: 20px;">
        <label class="custom-file-upload" style="
            display: block;
            width: 100%;
            height: 60px;
            background-color: #3498db;
            color: white;
            text-align: center;
            line-height: 60px;
            font-size: 20px;
            font-weight: bold;
            border-radius: 12px;
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">
            {button_text}
            <input type="file" accept="image/*" capture="environment" id="{key_id}" style="display: none;">
        </label>
        <div id="status_{key_id}" style="margin-top: 5px; font-size: 14px; color: #7f8c8d;"></div>
    </div>

    <script>
    const fileInput_{key_id} = document.getElementById('{key_id}');
    fileInput_{key_id}.addEventListener('change', function(e) {{
        const file = e.target.files[0];
        if (!file) return;
        
        document.getElementById('status_{key_id}').innerText = "⚡ 현장 사진 초고속 압축 중...";
        
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = function(event) {{
            const img = new Image();
            img.src = event.target.result;
            img.onload = function() {{
                // 초고화질 사진을 가로 600px 레이아웃으로 강제 다이어트
                const maxWidth = 600;
                const scaleFactor = maxWidth / img.width;
                const canvas = document.createElement('canvas');
                canvas.width = maxWidth;
                canvas.height = img.height * scaleFactor;
                
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                
                // 압축된 가벼운 이미지만 추출 (용량이 1/50로 줄어듦)
                const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
                
                // Streamlit 서버로 가벼워진 이미지 데이터 전송
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    value: dataUrl,
                    key: '{key_id}'
                }}, '*');
                document.getElementById('status_{key_id}').innerText = "📸 전송 완료!";
            }}
        }}
    }});
    </script>
    """
    return st.components.v1.html(html_code, height=95)

# UI 디자인 고도화
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

# ==========================================
# 2. 상단 헤더 영역
# ==========================================
st.image("nongshim_logo.png", width=150)
st.title("🍜 부산생산1팀 일부인 검증 시스템")
st.caption("촬영 즉시 실시간 전하 압축 알고리즘 탑재 버전 (V4.0 - 완결판)")
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

def extract_pure_marking(raw_text):
    date_match = re.search(r'\d{8}', raw_text)
    date_part = date_match.group(0) if date_match else ""
    remaining_text = raw_text.replace(date_part, "")
    lot_matches = re.findall(r'[A-Z0-9]{2,6}', remaining_text)
    lot_part = lot_matches[0] if lot_matches else ""
    if date_part:
        return f"{date_part} {lot_part}".strip()
    return raw_text

def decode_image_base64(base64_str):
    if not base64_str:
        return None, ""
    header, encoded = base64_str.split(",", 1)
    data = base64.b64decode(encoded)
    img = Image.open(BytesIO(data))
    img_np = np.array(img)
    result = reader.readtext(img_np, detail=0)
    raw_combined = "".join(result).upper().replace(" ", "")
    pure_marking = extract_pure_marking(raw_combined)
    return img, pure_marking

# ==========================================
# 4. 현장 작업용 투트랙 레이아웃 구성
# ==========================================
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🎯 1단계: [기준] 마스터 등록")
    # 자바스크립트 특제 카메라 버튼 배치
    master_b64 = HTML5_Camera_Compressor("master_cam", "📸 즉시 카메라 촬영 [기준]")
    
    master_text = ""
    if master_b64:
        m_img, master_text = decode_image_base64(master_b64)
        if m_img:
            st.image(m_img, caption="🎯 등록된 기준 데이터", use_container_width=True)

with col2:
    st.markdown("### 🔍 2단계: [검사] 매시간 대조")
    # 자바스크립트 특제 카메라 버튼 배치
    test_b64 = HTML5_Camera_Compressor("test_cam", "📸 즉시 카메라 촬영 [검사]")
    
    test_text = ""
    if test_b64:
        t_img, test_text = decode_image_base64(test_b64)
        if t_img:
            st.image(t_img, caption="🔍 방금 촬영된 검사 대상", use_container_width=True)

# ==========================================
# 5. 실시간 비교 및 최종 판정
# ==========================================
st.write("---")
st.subheader("📊 AI 1:1 대조 판정 결과")

if master_b64 and test_b64:
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(label="🎯 순수 기준 데이터", value=master_text if master_text else "인식 실패")
    with res_col2:
        st.metric(label="🔍 순수 검사 데이터", value=test_text if test_text else "인식 실패")
    
    st.write("")
    
    if master_text == test_text and master_text != "":
        st.markdown(
            '<p class="big-font-ok">🟢 일치 (OK) <br><span style="font-size:16px; font-weight:normal;">일부인이 완벽히 일치합니다. 생산을 계속 진행하세요.</span></p>', 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<p class="big-font-ng">🔴 불일치 (NG) - 오날인 위험!! <br><span style="font-size:16px; font-weight:normal;">날짜나 로트번호 패턴이 다릅니다! 마킹기를 확인하세요.</span></p>', 
            unsafe_allow_html=True
        )
else:
    st.warning("💡 판정을 시작하려면 좌측 [기준] 버튼과 우측 [검사] 버튼을 눌러 카메라로 즉시 촬영해 주세요.")
