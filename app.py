import io
from datetime import datetime

import streamlit as st
from PIL import Image
from google import genai

APP_NAME = "AI 蝦皮自動化"
APP_VERSION = "2.5 PRO"

st.set_page_config(
    page_title=f"{APP_NAME} {APP_VERSION}",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- CSS 樣式 --------------------
st.markdown("""
<style>
.stApp{background:radial-gradient(circle at 20% 0%,rgba(255,90,0,.08),transparent 25%),#05080d;color:#f5f7fa}
#MainMenu,footer{visibility:hidden}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0a1018,#070b11);border-right:1px solid rgba(255,255,255,.08)}
.card{background:linear-gradient(145deg,#101923,#090f17);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:16px;margin-bottom:14px}
.title{font-size:24px;font-weight:800}.sub{color:#8995a4;font-size:12px}
.section{font-size:17px;font-weight:800;margin:10px 0}
.badge{display:inline-block;margin-left:8px;padding:3px 8px;border-radius:6px;font-size:11px;color:#ff9d52;border:1px solid #ff6a00;background:rgba(255,90,0,.1)}
.metric{background:linear-gradient(145deg,#111a25,#0b1119);border:1px solid rgba(255,255,255,.07);border-radius:13px;padding:13px;min-height:80px}
.metric-label{font-size:11px;color:#8995a4}.metric-value{font-size:21px;font-weight:800;margin-top:4px}.orange{color:#ff6a00}.green{color:#50d890}.blue{color:#4ab7ff}.purple{color:#b28cff}
.workflow{display:flex;gap:8px;align-items:center;background:#0b121b;border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:12px;margin-bottom:14px;overflow-x:auto}
.step{min-width:130px;flex:1;background:#101923;border:1px solid rgba(255,255,255,.08);border-radius:11px;padding:10px}.step-icon{font-size:22px}.step-title{font-size:13px;font-weight:800}.step-desc{font-size:10px;color:#7e8a99}.arrow{color:#ff6a00;font-size:20px;font-weight:bold}
.check{color:#49d98c}.tag{display:inline-block;padding:5px 9px;margin:3px;background:#172331;border:1px solid #293a4b;border-radius:7px;color:#b8c5d2;font-size:11px}
.stButton>button{border-radius:8px!important;background:#111a24!important;color:#fff!important;font-weight:700!important;border:1px solid rgba(255,255,255,.12)!important}
.stButton>button:hover{border-color:#ff6a00!important;color:#ff8b42!important}
.stTextInput input,.stNumberInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"]>div{background:#0b121b!important;color:#fff!important;border-radius:8px!important}
</style>
""", unsafe_allow_html=True)

# -------------------- Gemini 安全讀取 --------------------
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
        client = genai.Client(api_key=api_key)
        contents = [prompt_text]
        if image_file:
            img = Image.open(image_file)
            contents.append(img)
            
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents
        )
        return response.text
    except Exception as e:
        st.error(f"❌ API 呼叫失敗：{str(e)}")
        return None

# -------------------- State 初始化 --------------------
def init_state():
    defaults = {
        "page": "商品上架工作台",
        "product_name": "",
        "category": "保養保健",
        "price": 499,
        "stock": 100,
        "selling_points": "",
        "condition": "全新",
        "images": [],
        "generated": False,
        "published": 0,
        "history": [],
        "gemini_api_key": "",
        "ai_title": "",
        "ai_desc": "",
        "ai_keywords": "",
        "ai_tiktok": "",
        "ai_jimeng": "",
        "ai_analysis": ""
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

def current_name():
    return st.session_state.product_name.strip() or "玻尿酸保濕精華液"

def save_history(action):
    st.session_state.history.insert(0, {
        "時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "商品": current_name(),
        "操作": action,
    })

# -------------------- 側邊欄 --------------------
def sidebar():
    with st.sidebar:
        st.markdown('<div class="card"><div style="font-size:19px;font-weight:800">🛍️ AI 蝦皮自動化</div><div class="sub">AI 智能生成・一鍵上架</div></div>', unsafe_allow_html=True)
        menus = [
            ("🏠", "Dashboard"), ("🛍️", "商品上架工作台"), ("📦", "商品管理"),
            ("🧾", "訂單管理"), ("📊", "數據分析"), ("🖼️", "AI 素材庫"),
            ("🕘", "歷史紀錄"), ("🎵", "TikTok 短影音"), ("💰", "蝦皮分潤管理"),
        ]
        for icon, name in menus:
            if st.button(f"{icon}  {name}", key=f"nav_{name}", use_container_width=True):
                st.session_state.page = name
                st.rerun()
        st.markdown("---")
        for icon, name in [("👤", "會員管理"), ("🛡️", "管理員中心"), ("⚙️", "系統設定"), ("🔑", "API 設定"), ("📚", "使用教學")]:
            if st.button(f"{icon}  {name}", key=f"sys_{name}", use_container_width=True):
                st.session_state.page = name
                st.rerun()

# -------------------- 頁面 --------------------
def workspace():
    left, middle, right = st.columns([1.05, 1.25, 1.2])
    with left:
        st.markdown('<div class="card"><b>① 商品資訊輸入</b>', unsafe_allow_html=True)
        name = st.text_input("商品名稱", value=st.session_state.product_name, placeholder="例：玻尿酸保濕精華液")
        category = st.selectbox("商品分類", ["保養保健", "美妝保養", "3C 電子", "居家生活", "服飾鞋包"], index=0)
        price = st.number_input("商品價格", min_value=0, value=int(st.session_state.price))
        stock = st.number_input("商品庫存", min_value=0, value=int(st.session_state.stock))
        points = st.text_area("商品賣點", value=st.session_state.selling_points, placeholder="例：深層保濕、清爽", height=80)
        files = st.file_uploader("上傳商品圖片", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
        if files:
            st.session_state.images = files
            
        if st.button("⚡ 執行 AI 一鍵全部生成", use_container_width=True):
            st.session_state.product_name = name
            st.session_state.category = category
            st.session_state.price = price
            st.session_state.stock = stock
            st.session_state.selling_points = points
            
            with st.spinner("🚀 AI 正在一鍵分析圖片並自動產生標題、描述、關鍵字、短影音與圖片 Prompt..."):
                img_file = st.session_state.images[0] if st.session_state.images else None
                prompt = f"""請擔任蝦皮電商頂級行銷專家。針對商品「{current_name()}」（分類：{category}、價格：{price}、賣點：{points}），請一次產生以下 5 項內容，並用格式「---」分隔：
1. 蝦皮爆款商品標題（包含Emoji與熱搜詞，60字以內）
2. 蝦皮吸引人的商品描述（含商品特色、注意事項）
3. 搜尋關鍵字標籤（以逗號分隔，例如：保濕,精華液,修護）
4. TikTok 9:16 短影音15秒劇本
5. 即夢 AI (Jimeng AI) 2.5 英文商業產品攝影 Prompt"""

                res = call_gemini_api(prompt, img_file)
                if res:
                    parts = res.split("---")
                    st.session_state.ai_title = parts[0].strip() if len(parts) > 0 else f"🔥【熱銷爆款】{current_name()}"
                    st.session_state.ai_desc = parts[1].strip() if len(parts) > 1 else res
                    st.session_state.ai_keywords = parts[2].strip() if len(parts) > 2 else "熱銷,推薦,正品"
                    st.session_state.ai_tiktok = parts[3].strip() if len(parts) > 3 else f"🔥 {current_name()}\n熱銷推薦中！"
                    st.session_state.ai_jimeng = parts[4].strip() if len(parts) > 4 else f"Commercial product photo of {current_name()}, 8k, photorealistic"
                    st.session_state.ai_analysis = "AI 已經自動解析商品特徵並完成全套文案創作！"
                    save_history("一鍵生成全套行銷內容")
                    st.success("✅ 一鍵生成完畢！請至右側查看與微調結果。")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with middle:
        st.markdown('<div class="card"><b>② AI 分析結果</b>', unsafe_allow_html=True)
        if st.session_state.images:
            try:
                st.image(Image.open(st.session_state.images[0]), use_container_width=True)
            except Exception:
                pass
        st.write(st.session_state.ai_analysis or "請點擊「⚡ 執行 AI 一鍵全部生成」按鈕。")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with right:
        st.markdown('<div class="card"><b>③ AI 內容一鍵成果</b>', unsafe_allow_html=True)
        tabs = st.tabs(["商品標題", "商品描述", "關鍵字", "TikTok 腳本", "即夢 Prompt"])
        with tabs[0]:
            st.text_area("標題", st.session_state.ai_title, height=100)
        with tabs[1]:
            st.text_area("描述", st.session_state.ai_desc, height=220)
        with tabs[2]:
            st.text_area("關鍵字", st.session_state.ai_keywords, height=80)
        with tabs[3]:
            st.text_area("TikTok", st.session_state.ai_tiktok, height=180)
        with tabs[4]:
            st.text_area("即夢 AI Prompt", st.session_state.ai_jimeng, height=180)
        st.markdown('</div>', unsafe_allow_html=True)

def generic_page(page):
    if page == "API 設定":
        st.markdown('<div class="card"><b>🔑 API 設定</b></div>', unsafe_allow_html=True)
        key = st.text_input("請貼上您的 Gemini API Key", value=st.session_state.gemini_api_key, type="password")
        if key != st.session_state.gemini_api_key:
            st.session_state.gemini_api_key = key
            st.success("✅ API Key 儲存成功！現在可以前往「商品上架工作台」進行一鍵生成了！")
    else:
        st.info(f"{page} 頁面運作中...")

# -------------------- 主流程 --------------------
sidebar()
st.markdown('<div class="card"><div class="title">🛍️ AI 蝦皮自動化 <span class="badge">2.5 PRO</span></div></div>', unsafe_allow_html=True)

if st.session_state.page == "商品上架工作台":
    workspace()
else:
    generic_page(st.session_state.page)
