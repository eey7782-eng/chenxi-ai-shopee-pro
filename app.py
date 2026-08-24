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

st.markdown("""
<style>
.stApp{background:radial-gradient(circle at 20% 0%,rgba(255,90,0,.08),transparent 25%),#05080d;color:#f5f7fa}
#MainMenu,footer{visibility:hidden}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0a1018,#070b11);border-right:1px solid rgba(255,255,255,.08)}
.card{background:linear-gradient(145deg,#101923,#090f17);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:16px;margin-bottom:14px}
.title{font-size:24px;font-weight:800}.sub{color:#8995a4;font-size:12px}
.section{font-size:17px;font-weight:800;margin:10px 0}
.# -------------------- Gemini API 邏輯 --------------------
def get_effective_api_key():
    """優先讀取 UI 設定，次之讀取 Streamlit Secrets"""
    if st.session_state.get("gemini_api_key"):
        return st.session_state["gemini_api_key"]
    try:
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return ""

def call_gemini_api(prompt_text, image_file=None):
    """呼叫 Gemini 2.5 Flash 生成內容"""
    api_key = get_effective_api_key()
    if not api_key:
        st.error("❌ 未檢測到有效的 Gemini API Key！請至 Secrets 或 [API 設定] 填寫。")
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

# -------------------- helpers --------------------
def current_name():
    return st.session_state.product_name.strip() or "玻尿酸保濕精華液"

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
        st.markdown('<div class="card"><b style="color:#ff8a3d">👑 PRO 會員</b><br><span class="check">✓</span> Gemini 2.5 API 連線<br><span class="check">✓</span> 商品圖片分析介面<br><span class="check">✓</span> TikTok 9:16<br><span class="check">✓</span> 即夢 Prompt<br><span class="check">✓</span> 歷史紀錄</div>', unsafe_allow_html=True)

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
            
            with st.spinner("✨ Gemini AI 分析並撰寫銷售文案中..."):
                img_file = st.session_state.images[0] if st.session_state.images else None
                prompt = f"請為商品「{current_name()}」（分類：{category}、價格：{price}、賣點：{points}）撰寫包含 Emoji 的爆款蝦皮標題、銷售描述、搜尋關鍵字、TikTok 短影音腳本與即夢 AI 圖片提示詞。請用清晰段落分隔。"
                res = call_gemini_api(prompt, img_file)
                if res:
                    st.session_state.ai_desc = res
                    st.session_state.ai_title = f"🔥爆款推薦｜{current_name()}｜高CP值正品"
                    st.session_state.ai_keywords = "保濕,補水,修護,保養,熱銷,推薦"
                    st.session_state.ai_tiktok = f"🔥 {current_name()}\n\n這款超讚！點擊選購！"
                    st.session_state.ai_jimeng = f"Product shot of {current_name()}, 8k, photorealistic"
                    st.session_state.ai_analysis = "AI 已完成圖片與商品賣點特徵分析。"
                    st.session_state.generated = True
                    save_history("執行 AI 工作流")
                    st.success("AI 工作流完成！內容已更新！")
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
            st.write(st.session_state.ai_analysis or "請點擊「執行 AI 工作流」觸發 Gemini 分析。")
        with tabs[1]:
            st.checkbox(st.session_state.ai_title or f"【爆款】{current_name()}", value=True)
        with tabs[2]:
            kw_list = st.session_state.ai_keywords.split(",") if st.session_state.ai_keywords else ["熱銷", "推薦"]
            st.markdown("".join(f'<span class="tag">#{x}</span>' for x in kw_list), unsafe_allow_html=True)
        with tabs[3]:
            st.markdown(f'<div><span class="check">✓</span> {points or "高效保濕"}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with right:
        st.markdown('<div class="card"><b>③ AI 內容生成</b>', unsafe_allow_html=True)
        tabs = st.tabs(["商品標題", "商品描述", "關鍵字", "TikTok 文案", "即夢 Prompt"])
        with tabs[0]:
            st.text_area("標題", st.session_state.ai_title, height=120)
        with tabs[1]:
            st.text_area("描述", st.session_state.ai_desc, height=200)
        with tabs[2]:
            st.text_area("關鍵字", st.session_state.ai_keywords, height=90)
        with tabs[3]:
            st.text_area("TikTok", st.session_state.ai_tiktok, height=170)
        with tabs[4]:
            st.text_area("即夢 AI Prompt", st.session_state.ai_jimeng, height=260)
        st.markdown('</div>', unsafe_allow_html=True)
        
    bottom1, bottom2, bottom3 = st.columns([1, 1.2, 1])
    with bottom1:
        st.markdown('<div class="card"><b>④ 蝦皮上架設定</b>', unsafe_allow_html=True)
        st.selectbox("物流", ["蝦皮店到店", "7-11 店到店", "全家店到店", "賣家宅配"])
        st.selectbox("出貨地", ["台灣・新北市", "台灣・台北市", "台灣・桃園市"])
        st.text_input("商品規格", "預設規格")
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
        has_key = "🟢 已連線" if get_effective_api_key() else "🔴 未設定 API Key"
        st.markdown(f'<div class="card"><b>系統狀態</b><h2>🟢 正常</h2>AI：{has_key}<br>圖片：{len(st.session_state.images)} 張<br>模擬上架：{st.session_state.published} 次<br>版本：{APP_VERSION}</div>', unsafe_allow_html=True)

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
    
    if page == "API 設定":
        st.info("可以在此輸入 Gemini API Key，或在 Streamlit Secrets 中設定 GEMINI_API_KEY。")
        key = st.text_input("Gemini API Key", value=st.session_state.gemini_api_key, type="password")
        if key != st.session_state.gemini_api_key:
            st.session_state.gemini_api_key = key
            st.success("API Key 已更新！")
        st.text_input("Shopee API Key", type="password")
    elif page == "歷史紀錄":
        if st.session_state.history:
            st.dataframe(st.session_state.history, use_container_width=True, hide_index=True)
        else:
            st.info("尚無歷史紀錄。")
    elif page == "商品管理":
        st.dataframe({"商品":["玻尿酸保濕精華液","修護面膜","保濕乳液"],"價格":[499,299,399],"庫存":[100,250,88],"狀態":["上架中","上架中","草稿"]}, use_container_width=True, hide_index=True)
    elif page == "使用教學":
        st.markdown("""### 使用流程\n1. 輸入商品名稱、分類、價格、庫存。\n2. 上傳一張或多張商品圖片。\n3. 執行 AI 工作流。\n4. 檢查標題、描述、關鍵字、TikTok 文案與即夢 Prompt。\n5. 使用蝦皮預覽確認資料。\n6. 目前一鍵上架為**模擬功能**，尚未真的連接蝦皮。""")
    else:
        st.info(f"{page} 介面已建立。")

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
