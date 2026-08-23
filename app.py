import io
from datetime import datetime

import streamlit as st
from PIL import Image

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
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

# -------------------- helpers --------------------
def current_name():
    return st.session_state.product_name.strip() or "玻尿酸保濕精華液"

def title_text():
    return f"{current_name()}｜深層保濕修護｜日常補水保養"

def description_text():
    return f"""{current_name()}\n\n✨ 商品特色\n✓ 深層保濕補水\n✓ 修護日常保養\n✓ 溫和好使用\n✓ 清爽不黏膩\n\n實際商品資訊請以商品包裝及賣場資訊為準。"""

def keywords_text():
    return "保濕,補水,修護,保養,美容,肌膚,日常保養"

def tiktok_text():
    return f"""🔥 {current_name()}\n\n乾燥、缺水怎麼辦？\n用簡單的日常保養方式，維持水嫩感。\n\n✨ 商品特色展示\n🛒 想了解更多商品資訊，立即查看賣場！"""

def jimeng_prompt():
    return f"""9:16 vertical premium commercial product video.\n\nMain subject: {current_name()}\n\nUse the uploaded product image as the ONLY visual source for the product. Preserve original product shape, packaging, logo, label, colors, materials and visible text.\n\nCamera: slow cinematic push-in, subtle orbit movement, premium commercial lighting, clean luxury background.\n\nDo not redesign the product. Do not invent logos. Do not change packaging. Do not add fake text."""

def save_history(action):
    st.session_state.history.insert(0, {
        "時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "商品": current_name(),
        "操作": action,
    })

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
        for icon, name in [("👤", "會員管理"), ("🛡️", "管理員中心"), ("⚙️", "系統設定"), ("🔑", "API 設定"), ("📚", "使用教學")]:
            if st.button(f"{icon}  {name}", key=f"sys_{name}", use_container_width=True):
                st.session_state.page = name
                st.rerun()
        st.markdown('<div class="card"><b style="color:#ff8a3d">👑 PRO 會員</b><br><span class="check">✓</span> AI 內容生成<br><span class="check">✓</span> 商品圖片分析介面<br><span class="check">✓</span> TikTok 9:16<br><span class="check">✓</span> 即夢 Prompt<br><span class="check">✓</span> 歷史紀錄</div>', unsafe_allow_html=True)

# -------------------- header / metrics --------------------
def header():
    st.markdown('<div class="card"><div class="title">🛍️ AI 蝦皮自動化 <span class="badge">2.5 PRO</span></div><div class="sub">AI 智能生成・商品工作流・蝦皮上架準備</div></div>', unsafe_allow_html=True)

def metrics():
    cols = st.columns(4)
    values = [("今日 AI 使用額度", "86 / 200 次", "orange"), ("AI 剩餘額度", "1,248 Tokens", "green"), ("會員等級", "PRO 會員", "purple"), ("會員期限", "永久會員", "blue")]
    for col, (label, value, cls) in zip(cols, values):
        with col:
            st.markdown(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value {cls}">{value}</div></div>', unsafe_allow_html=True)

# -------------------- dashboard --------------------
def dashboard():
    st.markdown('<div class="section">📊 Dashboard 總覽</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    for col, icon, label, value, delta in zip(cols, ["🛍️", "👁️", "🛒", "💰"], ["今日上架商品", "商品瀏覽數", "成交訂單", "銷售額"], ["12", "5,689", "58", "NT$28,560"], ["+3", "+22%", "+15%", "+25%"]):
        with col:
            st.markdown(f'<div class="metric"><div style="font-size:23px">{icon}</div><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="green">{delta}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section">🚀 AI 自動化流程</div>', unsafe_allow_html=True)
    st.markdown('<div class="workflow">' + '<div class="step"><div class="step-icon">📝</div><div class="step-title">商品輸入</div><div class="step-desc">資料與圖片</div></div><div class="arrow">→</div><div class="step"><div class="step-icon">🧠</div><div class="step-title">AI 分析</div><div class="step-desc">分析商品</div></div><div class="arrow">→</div><div class="step"><div class="step-icon">✨</div><div class="step-title">內容生成</div><div class="step-desc">標題與文案</div></div><div class="arrow">→</div><div class="step"><div class="step-icon">⚙️</div><div class="step-title">上架設定</div><div class="step-desc">價格與庫存</div></div><div class="arrow">→</div><div class="step"><div class="step-icon">🚀</div><div class="step-title">一鍵上架</div><div class="step-desc">目前為模擬</div></div></div>', unsafe_allow_html=True)
    a, b = st.columns([2, 1])
    with a:
        st.markdown('<div class="card"><b>📈 最近銷售</b></div>', unsafe_allow_html=True)
        st.line_chart({"銷售額": [18000, 21000, 19500, 26000, 24500, 28000, 28560]})
    with b:
        st.markdown('<div class="card"><b>🤖 AI 使用統計</b><h1 style="color:#ff6a00">24.96%</h1>本月使用量<br><br>文案生成：658 次<br>圖片分析：412 次<br>其他功能：178 次</div>', unsafe_allow_html=True)

# -------------------- workspace --------------------
def workflow_header():
    st.markdown('<div class="workflow"><div class="step"><div class="step-icon">📝</div><div class="step-title">商品資訊</div><div class="step-desc">輸入商品</div></div><div class="arrow">→</div><div class="step"><div class="step-icon">🧠</div><div class="step-title">AI 分析</div><div class="step-desc">分析圖片與資料</div></div><div class="arrow">→</div><div class="step"><div class="step-icon">✨</div><div class="step-title">內容生成</div><div class="step-desc">文案與 Prompt</div></div><div class="arrow">→</div><div class="step"><div class="step-icon">🚀</div><div class="step-title">上架</div><div class="step-desc">目前為模擬</div></div></div>', unsafe_allow_html=True)

def workspace():
    workflow_header()
    left, middle, right = st.columns([1.05, 1.25, 1.2])
    with left:
        st.markdown('<div class="card"><b>① 商品資訊輸入</b>', unsafe_allow_html=True)
        name = st.text_input("商品名稱", value=st.session_state.product_name, placeholder="例如：玻尿酸保濕精華液 30ml")
        category = st.selectbox("商品分類", ["保養保健", "美妝保養", "3C 電子", "居家生活", "服飾鞋包", "食品飲料", "汽機車", "其他"], index=0)
        price = st.number_input("商品價格", min_value=0, value=int(st.session_state.price), step=10)
        stock = st.number_input("商品庫存", min_value=0, value=int(st.session_state.stock), step=1)
        condition = st.radio("商品狀態", ["全新", "二手"], horizontal=True)
        points = st.text_area("商品賣點", value=st.session_state.selling_points, placeholder="例如：深層保濕、修護、溫和", height=90)
        files = st.file_uploader("上傳商品圖片（可多張）", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
        if files:
            st.session_state.images = files
            st.success(f"已選擇 {len(files)} 張圖片")
        if st.button("🚀 執行 AI 工作流", use_container_width=True):
            st.session_state.product_name = name
            st.session_state.category = category
            st.session_state.price = price
            st.session_state.stock = stock
            st.session_state.condition = condition
            st.session_state.selling_points = points
            st.session_state.generated = True
            save_history("執行 AI 工作流")
            st.success("工作流完成，內容已產生")
        st.markdown('</div>', unsafe_allow_html=True)
    with middle:
        st.markdown('<div class="card"><b>② AI 分析結果</b>', unsafe_allow_html=True)
        tabs = st.tabs(["商品分析", "標題建議", "關鍵字", "賣點"])
        with tabs[0]:
            if st.session_state.images:
                try:
                    img = Image.open(st.session_state.images[0])
                    st.image(img, use_container_width=True)
                except Exception:
                    st.warning("圖片無法讀取")
            else:
                st.info("尚未上傳商品圖片")
            st.write(f"商品：{current_name()}")
            st.write("目前為離線展示模式；未連接 Gemini，因此不會虛構真正的圖片分析結果。")
        with tabs[1]:
            for i, text in enumerate([title_text(), f"{current_name()}｜保濕補水｜日常保養", f"高效修護 {current_name()}｜清爽好吸收"]):
                st.checkbox(text, value=(i == 0), key=f"suggest_{i}")
        with tabs[2]:
            st.markdown("".join(f'<span class="tag">#{x}</span>' for x in keywords_text().split(",")), unsafe_allow_html=True)
        with tabs[3]:
            for x in ["深層保濕補水", "日常修護", "溫和好使用", "清爽不黏膩"]:
                st.markdown(f'<div><span class="check">✓</span> {x}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="card"><b>③ AI 內容生成</b>', unsafe_allow_html=True)
        tabs = st.tabs(["商品標題", "商品描述", "關鍵字", "TikTok 文案", "即夢 Prompt"])
        with tabs[0]:
            st.text_area("標題", title_text(), height=120)
        with tabs[1]:
            st.text_area("描述", description_text(), height=200)
        with tabs[2]:
            st.text_area("關鍵字", keywords_text(), height=90)
        with tabs[3]:
            st.text_area("TikTok", tiktok_text(), height=170)
        with tabs[4]:
            st.text_area("即夢 AI 2.5 Prompt", jimeng_prompt(), height=260)
        st.markdown('</div>', unsafe_allow_html=True)
    bottom1, bottom2, bottom3 = st.columns([1, 1.2, 1])
    with bottom1:
        st.markdown('<div class="card"><b>④ 蝦皮上架設定</b>', unsafe_allow_html=True)
        st.selectbox("物流", ["蝦皮店到店", "7-11 店到店", "全家店到店", "賣家宅配"])
        st.selectbox("出貨地", ["台灣・新北市", "台灣・台北市", "台灣・桃園市"])
        st.text_input("商品規格", "30ml")
        st.number_input("上架庫存", min_value=0, value=int(st.session_state.stock))
        st.selectbox("出貨天數", ["1 天內出貨", "2 天內出貨", "3 天內出貨", "7 天內出貨"])
        st.toggle("自動回覆買家問題", True)
        st.markdown('</div>', unsafe_allow_html=True)
    with bottom2:
        st.markdown('<div class="card"><b>⑤ 蝦皮上架預覽</b>', unsafe_allow_html=True)
        if st.session_state.images:
            try:
                st.image(Image.open(st.session_state.images[0]), use_container_width=True)
            except Exception:
                st.info("圖片預覽失敗")
        else:
            st.info("尚未上傳商品圖片")
        st.markdown(f'<div style="background:#fff;color:#222;padding:12px;border-radius:9px"><b>{current_name()}</b><div style="color:#ee4d2d;font-size:25px;font-weight:800">NT${st.session_state.price}</div><small>⭐⭐⭐⭐⭐　預覽資料</small></div>', unsafe_allow_html=True)
        if st.button("🚀 一鍵上架蝦皮（模擬）", use_container_width=True):
            st.session_state.published += 1
            save_history("一鍵上架模擬")
            st.success("模擬上架完成；尚未連接蝦皮官方 API，不會真的發布商品。")
        st.markdown('</div>', unsafe_allow_html=True)
    with bottom3:
        st.markdown(f'<div class="card"><b>系統狀態</b><h2>🟢 正常</h2>AI：離線展示模式<br>圖片：{len(st.session_state.images)} 張<br>模擬上架：{st.session_state.published} 次<br>版本：{APP_VERSION}</div>', unsafe_allow_html=True)

# -------------------- generic pages --------------------
def generic_page(page):
    info = {
        "商品管理": ("📦", "管理商品資料與上架狀態"),
        "訂單管理": ("🧾", "管理訂單與出貨流程"),
        "數據分析": ("📊", "查看銷售與使用數據"),
        "AI 素材庫": ("🖼️", "管理圖片、影片與 Prompt"),
        "歷史紀錄": ("🕘", "查看操作歷史"),
        "TikTok 短影音": ("🎵", "建立 9:16 短影音內容"),
        "蝦皮分潤管理": ("💰", "查看分潤資料"),
        "會員管理": ("👤", "管理會員帳號與期限"),
        "管理員中心": ("🛡️", "管理系統權限"),
        "系統設定": ("⚙️", "系統功能設定"),
        "API 設定": ("🔑", "AI 與蝦皮 API 設定"),
        "使用教學": ("📚", "操作說明"),
    }
    icon, desc = info.get(page, ("⚙️", "系統功能"))
    st.markdown(f'<div class="card"><div style="font-size:28px">{icon}</div><div class="title">{page}</div><div class="sub">{desc}</div></div>', unsafe_allow_html=True)
    if page == "商品管理":
        st.dataframe({"商品":["玻尿酸保濕精華液","修護面膜","保濕乳液"],"價格":[499,299,399],"庫存":[100,250,88],"狀態":["上架中","上架中","草稿"]}, use_container_width=True, hide_index=True)
    elif page == "訂單管理":
        st.info("目前為介面展示版，尚未連接蝦皮訂單 API。")
    elif page == "數據分析":
        a,b,c=st.columns(3)
        a.metric("今日銷售額","NT$28,560","+25%")
        b.metric("今日訂單","58","+15%")
        c.metric("瀏覽人次","5,689","+22%")
        st.line_chart({"銷售額":[18000,21000,19500,26000,24500,28000,28560]})
    elif page == "AI 素材庫":
        st.info("素材庫介面已建立；目前資料只保存在本次 Streamlit 工作階段。")
    elif page == "歷史紀錄":
        if st.session_state.history:
            st.dataframe(st.session_state.history, use_container_width=True, hide_index=True)
        else:
            st.info("尚無歷史紀錄。")
    elif page == "TikTok 短影音":
        st.text_area("9:16 短影音腳本", tiktok_text(), height=180)
        st.text_area("即夢 AI 2.5 Prompt", jimeng_prompt(), height=230)
        st.info("目前只生成文字 Prompt，尚未連接影片生成服務。")
    elif page == "蝦皮分潤管理":
        st.metric("本月分潤","NT$12,580","+18%")
    elif page == "會員管理":
        st.info("會員管理介面已建立。正式登入與永久會員資料庫可在下一階段接入。")
    elif page == "管理員中心":
        st.warning("目前為展示介面，正式管理員驗證尚未連接資料庫。")
    elif page == "系統設定":
        st.toggle("啟用 AI 自動分析", True)
        st.toggle("自動保存歷史紀錄", True)
        st.toggle("深色科技介面", True)
    elif page == "API 設定":
        st.info("不填 API Key 也可以正常啟動本版本。")
        st.text_input("Gemini API Key", type="password")
        st.text_input("Shopee API Key", type="password")
    elif page == "使用教學":
        st.markdown("""### 使用流程\n1. 輸入商品名稱、分類、價格、庫存。\n2. 上傳一張或多張商品圖片。\n3. 執行 AI 工作流。\n4. 檢查標題、描述、關鍵字、TikTok 文案與即夢 Prompt。\n5. 使用蝦皮預覽確認資料。\n6. 目前一鍵上架為**模擬功能**，尚未真的連接蝦皮。""")

# -------------------- run --------------------
sidebar()
header()

if st.session_state.page == "Dashboard":
    dashboard()
elif st.session_state.page == "商品上架工作台":
    metrics()
    workspace()
else:
    generic_page(st.session_state.page)

st.markdown('<div style="text-align:center;color:#52606e;font-size:10px;padding:25px 0 10px">AI 蝦皮自動化 2.5 PRO ・ Streamlit Cloud Ready</div>', unsafe_allow_html=True)
