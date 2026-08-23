import io
import os
from datetime import datetime

import streamlit as st
from PIL import Image
import google.generativeai as genai

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

# -------------------- state --------------------
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
        # AI 生成結果儲存
        "ai_title": "",
        "ai_desc": "",
        "ai_keywords": "",
        "ai_tiktok": "",
        "ai_jimeng": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

# -------------------- helpers --------------------
def get_api_key():
    return st.secrets.get("GEMINI_API_KEY", "")

def save_history(action):
    st.session_state.history.insert(0, {
        "時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "商品": st.session_state.product_name or "未命名商品",
        "操作": action,
    })

def generate_all_ai_content(name, category, price, points, uploaded_files):
    api_key = get_api_key()
    if not api_key:
        st.error("❌ 找不到 Secrets API Key，請先設定 GEMINI_API_KEY！")
        return False

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
你是一位頂級蝦皮電商爆款專家與短影音導演。請根據以下商品資料，一次性生成完整的行銷與上架資料：

【商品名稱】：{name}
【商品分類】：{category}
【商品價格】：NT${price}
【特色賣點】：{points}

請完全照以下格式輸出（不要多加其他無關文字）：

===TITLE===
(請給出一個寫滿熱門搜尋關鍵字、吸引人的蝦皮商品標題，約 30-50 字)

===DESC===
(請給出條理分明、包含特色賣點、規格與溫馨提示的完整蝦皮商品描述)

===KEYWORDS===
(請給出 8-10 個用逗號分隔的精準搜尋關鍵字)

===TIKTOK===
(請給出適合 TikTok/Reels 的 30 秒帶貨短影音腳本，包含鏡頭畫面、旁白文案與強烈 CTA)

===JIMENG===
(請給出用於生成 9:16 商業產品影片的英文 AI 提示詞 Prompt，描述高品質光線、鏡頭動態與細節)
"""

    try:
        content_parts = [prompt]
        if uploaded_files:
            for file in uploaded_files:
                img = Image.open(file)
                content_parts.append(img)

        response = model.generate_content(content_parts)
        text = response.text

        # 解析結果
        title = text.split("===TITLE===")[1].split("===DESC===")[0].strip() if "===TITLE===" in text else ""
        desc = text.split("===DESC===")[1].split("===KEYWORDS===")[0].strip() if "===DESC===" in text else ""
        keywords = text.split("===KEYWORDS===")[1].split("===TIKTOK===")[0].strip() if "===KEYWORDS===" in text else ""
        tiktok = text.split("===TIKTOK===")[1].split("===JIMENG===")[0].strip() if "===TIKTOK===" in text else ""
        jimeng = text.split("===JIMENG===")[1].strip() if "===JIMENG===" in text else ""

        st.session_state.ai_title = title
        st.session_state.ai_desc = desc
        st.session_state.ai_keywords = keywords
        st.session_state.ai_tiktok = tiktok
        st.session_state.ai_jimeng = jimeng
        st.session_state.generated = True
        return True
    except Exception as e:
        st.error(f"AI 生成過程失敗：{e}")
        return False

# -------------------- sidebar --------------------
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
        if get_api_key():
            st.success("✅ Secrets API Key 已自動載入")
        else:
            st.error("⚠️ 未偵測到 Secrets Key")

# -------------------- header / metrics --------------------
def header():
    st.markdown('<div class="card"><div class="title">🛍️ AI 蝦皮自動化 <span class="badge">2.5 PRO 全自動一鍵生成版</span></div><div class="sub">AI 智能分析・全套文案、短影音與 Prompt 一鍵搞定</div></div>', unsafe_allow_html=True)

# -------------------- workspace --------------------
def workspace():
    left, middle, right = st.columns([1.05, 1.25, 1.2])
    with left:
        st.markdown('<div class="card"><b>① 輸入商品資訊</b>', unsafe_allow_html=True)
        name = st.text_input("商品名稱", value=st.session_state.product_name, placeholder="例如：玻尿酸保濕精華液")
        category = st.selectbox("商品分類", ["保養保健", "美妝保養", "3C 電子", "居家生活", "服飾鞋包", "食品飲料", "其他"], index=0)
        price = st.number_input("商品價格", min_value=0, value=int(st.session_state.price), step=10)
        stock = st.number_input("商品庫存", min_value=0, value=int(st.session_state.stock), step=1)
        points = st.text_area("商品賣點（可選）", value=st.session_state.selling_points, placeholder="例如：深層保濕、清爽不黏膩", height=80)
        files = st.file_uploader("上傳商品圖片（可多張，AI 會進行視覺分析）", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
        if files:
            st.session_state.images = files

        # ⚡⚡⚡ 一鍵生成全部核心按鈕 ⚡⚡⚡
        if st.button("🚀 一鍵全自動生成（標題+描述+關鍵字+短影音+Prompt）", type="primary", use_container_width=True):
            if not name and not files:
                st.warning("請至少填寫商品名稱或上傳商品圖片！")
            else:
                with st.spinner("🤖 Gemini AI 正在深度分析商品並一次生成全套素材..."):
                    st.session_state.product_name = name
                    st.session_state.category = category
                    st.session_state.price = price
                    st.session_state.stock = stock
                    st.session_state.selling_points = points
                    
                    if generate_all_ai_content(name, category, price, points, files):
                        save_history("一鍵全自動生成")
                        st.success("🎉 全套內容一鍵生成完成！")
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with middle:
        st.markdown('<div class="card"><b>② AI 圖片與商品視覺分析</b>', unsafe_allow_html=True)
        if st.session_state.images:
            try:
                img = Image.open(st.session_state.images[0])
                st.image(img, use_container_width=True)
            except Exception:
                st.warning("圖片讀取失敗")
        else:
            st.info("💡 尚未上傳商品圖片（可直接使用文字生成）")
        
        if st.session_state.generated:
            st.markdown("#### 🎯 關鍵字標籤")
            tags = st.session_state.ai_keywords.replace("\n", "").split(",")
            st.markdown("".join(f'<span class="tag">#{x.strip()}</span>' for x in tags if x.strip()), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card"><b>③ 一鍵生成結果列表</b>', unsafe_allow_html=True)
        tabs = st.tabs(["📌 商品標題", "📝 商品描述", "🏷️ 關鍵字", "🎵 TikTok 短影音", "🎬 即夢 AI Prompt"])
        with tabs[0]:
            st.text_area("生成的蝦皮標題", st.session_state.ai_title, height=120)
        with tabs[1]:
            st.text_area("生成的商品描述", st.session_state.ai_desc, height=220)
        with tabs[2]:
            st.text_area("關鍵字標籤", st.session_state.ai_keywords, height=100)
        with tabs[3]:
            st.text_area("TikTok/Reels 帶貨腳本", st.session_state.ai_tiktok, height=200)
        with tabs[4]:
            st.text_area("即夢 AI 2.5 影片 Prompt", st.session_state.ai_jimeng, height=220)
        st.markdown('</div>', unsafe_allow_html=True)

# -------------------- generic pages --------------------
def generic_page(page):
    st.markdown(f'<div class="card"><div class="title">{page}</div></div>', unsafe_allow_html=True)

# -------------------- run --------------------
sidebar()
header()

if st.session_state.page == "商品上架工作台":
    workspace()
else:
    generic_page(st.session_state.page)

st.markdown('<div style="text-align:center;color:#52606e;font-size:10px;padding:25px 0 10px">AI 蝦皮自動化 2.5 PRO ・ 全自動一鍵生成版</div>', unsafe_allow_html=True)
