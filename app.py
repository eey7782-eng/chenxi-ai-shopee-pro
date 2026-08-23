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

st.markdown('<div style="text-align:center;color:#52606e;font-size:10px;padding:25px 0 10px">AI 蝦皮自動化 2.5 PRO ・ 全自動一鍵生成版</div>', unsafe_allow_html=True)ate.stock = stock
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

