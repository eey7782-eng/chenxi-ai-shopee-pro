import io
from datetime import datetime

import streamlit as st
from PIL import Image

# 嘗試載入 Gemini SDK
try:
    from google import genai
    USE_NEW_SDK = True
except ImportError:
    import google.generativeai as genai
    USE_NEW_SDK = False

APP_NAME = "AI 蝦皮自動化"
APP_VERSION = "2.5 PRO"

st.set_page_config(
    page_title=f"{APP_NAME} {APP_VERSION}",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp{background:radial-gradient(circle at 20% 0%,rgba(255,90,0,.08),transparent 25%),#05080d;color:#f5f7fa}
#MainMenu,footer{visibility:hidden}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0a1018,#070b11);border-right:1px solid rgba(255,255,255,.08)}
.card{background:linear-gradient(145deg,#101923,#090f17);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:16px;margin-bottom:14px}
.title{font-size:24px;font-weight:800}.sub{color:#8995a4;font-size:12px}
.section{font-size:17px;font-weight:800;margin:10px 0}
.badge{display:inline-block;margin-left:8px;padding:3px 8px;border-radius:6px;font-size:11px;color:#ff9d52;border:1px solid #ff6a00;background:rgba(255,90,0,.1)}
.stButton>button{border-radius:8px!important;background:#111a24!important;color:#fff!important;font-weight:700!important;border:1px solid rgba(255,255,255,.12)!important}
.stButton>button:hover{border-color:#ff6a00!important;color:#ff8b42!important}
.stTextInput input,.stNumberInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"]>div{background:#0b121b!important;color:#fff!important;border-radius:8px!important}
</style>
""", unsafe_allow_html=True)

def get_effective_api_key():
    if st.session_state.get("gemini_api_key"):
        return st.session_state["gemini_api_key"]
    try:
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return ""

def call_gemini_api(prompt_text, image_file=None):
    api_key = get_effective_api_key()
    if not api_key:
        st.error("❌ 請先在左側選單「🔑 API 設定」中輸入您的 Gemini API Key！")
        return None
    try:
        if USE_NEW_SDK:
            client = genai.Client(api_key=api_key)
            contents = [prompt_text]
            if image_file:
                contents.append(Image.open(image_file))
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents
            )
            return response.text
        else:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            contents = [prompt_text]
            if image_file:
                contents.append(Image.open(image_file))
            response = model.generate_content(contents)
            return response.text
    except Exception as e:
        st.error(f"❌ API 呼叫失敗：{str(e)}")
        return None

def init_state():
    defaults = {
        "page": "商品上架工作台",
        "product_name": "",
        "category": "保養保健",
        "price": 499,
        "stock": 100,
        "selling_points": "",
        "images": [],
        "gemini_api_key": "",
        "ai_title": "",
        "ai_desc": "",
        "ai_keywords": "",
        "ai_tiktok": "",
        "ai_jimeng": ""
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

def current_name():
    return st.session_state.product_name.strip() or "玻尿酸保濕精華液"

# 側邊欄
with st.sidebar:
    st.markdown('<div class="card"><div style="font-size:19px;font-weight:800">🛍️ AI 蝦皮自動化</div></div>', unsafe_allow_html=True)
    if st.button("🛍️  商品上架工作台", use_container_width=True):
        st.session_state.page = "商品上架工作台"
        st.rerun()
    if st.button("🔑  API 設定", use_container_width=True):
        st.session_state.page = "API 設定"
        st.rerun()

st.markdown('<div class="card"><div class="title">🛍️ AI 蝦皮自動化 <span class="badge">2.5 PRO</span></div></div>', unsafe_allow_html=True)

if st.session_state.page == "商品上架工作台":
    left, right = st.columns([1, 1.2])
    with left:
        st.markdown('<div class="card"><b>① 商品資訊輸入</b>', unsafe_allow_html=True)
        name = st.text_input("商品名稱", value=st.session_state.product_name)
        category = st.selectbox("商品分類", ["保養保健", "美妝保養", "3C 電子", "居家生活", "服飾鞋包"])
        price = st.number_input("商品價格", min_value=0, value=int(st.session_state.price))
        points = st.text_area("商品賣點", value=st.session_state.selling_points)
        files = st.file_uploader("上傳商品圖片", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
        if files:
            st.session_state.images = files
            
        if st.button("⚡ 執行 AI 一鍵生成", use_container_width=True):
            st.session_state.product_name = name
            st.session_state.selling_points = points
            
            with st.spinner("🚀 AI 產生中..."):
                img_file = st.session_state.images[0] if st.session_state.images else None
                prompt = f"請為商品「{current_name()}」（分類：{category}、價格：{price}、賣點：{points}）撰寫包含 Emoji 的爆款蝦皮標題、銷售描述、關鍵字、TikTok 短影音腳本與即夢 Prompt，並用『---』分隔。"
                res = call_gemini_api(prompt, img_file)
                if res:
                    parts = res.split("---")
                    st.session_state.ai_title = parts[0].strip() if len(parts) > 0 else f"🔥【熱銷】{current_name()}"
                    st.session_state.ai_desc = parts[1].strip() if len(parts) > 1 else res
                    st.session_state.ai_keywords = parts[2].strip() if len(parts) > 2 else "熱銷,推薦"
                    st.session_state.ai_tiktok = parts[3].strip() if len(parts) > 3 else "短影音內容..."
                    st.session_state.ai_jimeng = parts[4].strip() if len(parts) > 4 else "Commercial photo"
                    st.success("✅ 生成完畢！")
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card"><b>② AI 一鍵成果</b>', unsafe_allow_html=True)
        st.text_area("標題", st.session_state.ai_title, height=80)
        st.text_area("描述", st.session_state.ai_desc, height=200)
        st.text_area("關鍵字", st.session_state.ai_keywords, height=70)
        st.text_area("TikTok 腳本", st.session_state.ai_tiktok, height=120)
        st.text_area("即夢 AI Prompt", st.session_state.ai_jimeng, height=120)
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == "API 設定":
    st.markdown('<div class="card"><b>🔑 API 設定</b></div>', unsafe_allow_html=True)
    key = st.text_input("請貼上您的 Gemini API Key", value=st.session_state.gemini_api_key, type="password")
    if key != st.session_state.gemini_api_key:
        st.session_state.gemini_api_key = key
        st.success("✅ API Key 儲存成功！")
