import streamlit as st
import easyocr
import numpy as np
from PIL import Image, ImageOps
import re
import base64
from io import BytesIO

# ==========================================
# 1. 페이지 설정 및 모바일 대형 UI 디자인
# ==========================================
st.set_page_config(page_title="농심 부산생산1팀 검증 시스템", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    div.stButton > button {
        width: 100% !important;
        height: 65px !important;
        font-size: 20px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
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
    </style>
""", unsafe_allow_html=True)

# [프론트엔드 핵심] 호출될 때마다 독립된 메모리를 생성하여 이전 사진 데이터를 완벽하게 덮어쓰는 압축 셔터
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
    // 클릭 시 무조건 폰의 기존 선택 기록을 강제로 지워버립니다.
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
                const maxWidth = 500;
                const scale = maxWidth / img.width;
                canvas.width = maxWidth;
                canvas.height = img.height * scale;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                
                // 30% 화질 압축으로 초경량화 도모 (튕김 방지)
                const dataUrl = canvas.toDataURL('image/jpeg', 0.3);
                window.parent.postMessage({{type: 'streamlit:setComponentValue', value: dataUrl, key: '{key_id}'}}, '*');
                document.getElementById('msg_{key_id}').innerText = "📸 전송 완료!";
            }}
        }}
    }});
    </script>
    """
    return st.components.v1.html(html_code, height=95)

# 상단 타이틀
st.image("nongshim_logo.png", width=140)
st.title("🍜 부산생산1팀 일부인 검증 시스템")
st.caption("메모리 꼬임 원천 제거 / 무단계 독립형 원터치 버전 (V10.0 - 청정 배포)")
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
        return ""
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
        return "AI 인식 오류"

# ==========================================
# 3. [혁신] 화면 고정형 독립 트랙 레이아웃
# ==========================================
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="title-box">🎯 [오더지/초물] 기준 등록</div>', unsafe_allow_html=True)
    # 한 번 세팅하면 새로고침 전까지 고정되는 독립형 컴포넌트
    master_b64 = HTML5_Single_Shutter("m_shutter", "🎯 기준 마스터 사진 촬영")
    
    if master_b64:
        st.session_state.final_m_b64 = master_b64
        m_pil = convert_b64_to_pil(master_b64)
        st.session_state.final_m_txt = extract_high_perf_marking(m_pil)

    # 등록된 기준 데이터 모니터링
    if "final_m_b64" in st.session_state and st.session_state.final_m_b64:
        st.image(convert_b64_to_pil(st.session_state.final_m_b64), caption=f"🎯 기준 매칭값: {st.session_state.final_m_txt}", use_container_width=True)

with col2:
    st.markdown('<div class="title-box">🔍 [매시간 제품] 실시간 검사</div>', unsafe_allow_html=True)
    # 버튼을 누를 때마다 이전 데이터를 무조건 새로 지우고 덮어쓰는 독립형 컴포넌트
    test_b64 = HTML5_Single_Shutter("t_shutter", "🔍 생산 제품 사진 촬영")
    
    if test_b64:
        st.session_state.final_t_b64 = test_b64
        t_pil = convert_b64_to_pil(test_b64)
        st.session_state.final_t_txt = extract_high_perf_marking(t_pil)

    # 촬영된 현재 제품 데이터 모니터링
    if "final_t_b64" in st.session_state and st.session_state.final_t_b64:
        st.image(convert_b64_to_pil(st.session_state.final_t_b64), caption=f"🔍 검사 매칭값: {st.session_state.final_t_txt}", use_container_width=True)

# ==========================================
# 4. 실시간 1:1 대조 판정 디스플레이
# ==========================================
st.write("---")
st.subheader("📊 AI 1:1 대조 판정 결과")

if "final_m_txt" in st.session_state and "final_t_txt" in st.session_state:
    m_res = st.session_state.final_m_txt
    t_res = st.session_state.final_t_txt
    
    if m_res != "" and t_res != "":
        if m_res == t_res and "실패" not in m_res:
            st.markdown(
                f'<p class="big-font-ok">🟢 일치 (OK) <br><span style="font-size:16px; font-weight:normal;">일부인이 완벽히 일치합니다. 생산을 계속 진행하세요.<br>({m_res})</span></p>', 
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<p class="big-font-ng">🔴 불일치 (NG) - 오날인 위험!! <br><span style="font-size:16px; font-weight:normal;">마킹 정보가 다릅니다! 마킹기 출력을 즉시 확인하세요.<br>🎯 기준: {m_res} / 🔍 검사: {t_res}</span></p>', 
                unsafe_allow_html=True
            )
else:
    st.info("💡 좌측 버튼으로 [기준 등록]을 먼저 하신 후, 우측 버튼으로 [생산 제품]을 촬영하시면 실시간 대조가 시작됩니다.")

# 화면 전체를 초기화하고 싶을 때만 누르는 완전 리셋 버튼
if st.button("🆕 시스템 전체 초기화 (제품 변경 시)"):
    st.session_state.clear()
    st.markdown("""<script>window.parent.location.reload();</script>""", unsafe_allow_html=True)
