import io
import os
import re
import json
import uuid
import hashlib
from pathlib import Path
from datetime import datetime, date

import streamlit as st
from PIL import Image, ImageOps

APP_NAME = "黑金剛 AI 多 AI 電商總控中心 PRO"
APP_VERSION = "4.0 FINAL"
DATA_DIR = Path("data")
MEDIA_DIR = DATA_DIR / "media"
HISTORY_DIR = DATA_DIR / "history"
MEMBERS_FILE = DATA_DIR / "members.json"
PRODUCTS_FILE = DATA_DIR / "products.json"
ORDERS_FILE = DATA_DIR / "orders.json"

MAX_IMAGE_SIZE = 1600
MAX_IMAGE_MB = 20
GEMINI_MODELS = ["gemini-3.7-flash", "gemini-3-flash-preview", "gemini-2.5-flash"]
ADMIN_USERNAME = "admin"

PAGES = [
    "🏠 Dashboard", "🤖 AI Agent 總控", "🛒 商品上架工作台", "📦 商品管理",
    "🧾 訂單管理", "📊 數據分析", "💰 利潤／蝦皮分潤", "🎬 TikTok 短影音",
    "🖼️ AI 圖片素材", "🎥 即夢 AI 2.5", "📚 AI 素材庫", "🕘 歷史紀錄",
    "👥 會員／管理中心", "⚙️ AI 設定"
]

AGENTS = {
    "🧠 總控 Agent": "任務拆解、Agent 路由、結果整合",
    "🔍 商品視覺分析 Agent": "商品圖片分析與真實性約束",
    "🛒 蝦皮上架 Agent": "標題、描述、規格、賣點、關鍵字",
    "💰 定價 Agent": "成本、售價、平台費、利潤",
    "📦 商品管理 Agent": "商品資料、庫存與狀態",
    "📊 電商數據 Agent": "訂單、營收、成本、毛利分析",
    "💵 分潤 Agent": "平台費、廣告費、其他成本",
    "✍️ 文案 Agent": "商品、促銷、廣告文案",
    "🔥 行銷 Agent": "促銷與轉換角度",
    "🎯 SEO Agent": "搜尋關鍵字與標題優化",
    "🎬 TikTok Agent": "Hook、腳本、CTA",
    "🎥 短影音導演 Agent": "分鏡、鏡位、運鏡、節奏",
    "🧩 即夢 Agent": "即夢 AI 2.5 Prompt",
    "🖼️ 圖片 Agent": "主圖、介紹圖、廣告圖 Prompt",
    "📱 社群 Agent": "TikTok、IG、FB 內容",
    "🛍️ 選品 Agent": "商品定位與賣點",
    "👤 消費者 Agent": "目標客群與購買動機",
    "🧠 競品 Agent": "競品比較與差異化角度",
    "📢 廣告 Agent": "廣告素材與文案方向",
    "💬 客服 Agent": "FAQ 與客服話術",
    "📝 評價 Agent": "評價優缺點整理",
    "🔄 內容再利用 Agent": "一份資料轉多平台內容",
    "📚 知識 Agent": "商品知識與 Prompt 規則",
    "🗂️ 素材管理 Agent": "素材分類與版本",
    "🕘 歷史 Agent": "任務與 AI 產出保存",
    "🔌 AI 路由 Agent": "Gemini／DeepSeek／Ollama 等路由",
    "🧪 品質檢查 Agent": "格式與內容品質檢查",
    "🛡️ 真實性 Agent": "防止捏造品牌、規格、功效",
    "📋 工作流 Agent": "多步驟任務串接",
}

TRUTH_RULE = """商品圖片是唯一視覺真實來源。不得自行捏造或補全圖片中不可確認的品牌、Logo、包裝、文字、顏色、材質、規格、容量、成分、功效、認證或數字。若無法確認，必須標示『無法由圖片確認』。"""


def ensure_dirs():
    for p in (DATA_DIR, MEDIA_DIR, HISTORY_DIR):
        p.mkdir(parents=True, exist_ok=True)


def load_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_members():
    members = load_json(MEMBERS_FILE, [])
    if not any(x.get("username") == ADMIN_USERNAME for x in members):
        members.append({"username": ADMIN_USERNAME, "password": hash_password("admin123"), "role": "admin", "expires": "2099-12-31"})
        save_json(MEMBERS_FILE, members)
    return members


def process_image(uploaded):
    raw = uploaded.getvalue()
    if len(raw) > MAX_IMAGE_MB * 1024 * 1024:
        raise ValueError(f"圖片超過 {MAX_IMAGE_MB} MB")
    img = Image.open(io.BytesIO(raw))
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=92)
    return img, out.getvalue()


def get_api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        key = ""
    return key or os.getenv("GEMINI_API_KEY", "")


def gemini_generate(prompt, image_bytes=None):
    key = get_api_key()
    if not key:
        return None, "尚未設定 GEMINI_API_KEY，已切換本地模板模式。"
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key)
        contents = [prompt]
        if image_bytes:
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))
        last_error = ""
        for model in GEMINI_MODELS:
            try:
                response = client.models.generate_content(model=model, contents=contents)
                text = getattr(response, "text", None)
                if text:
                    st.session_state["gemini_model"] = model
                    return text, None
            except Exception as e:
                last_error = str(e)
        return None, f"Gemini 呼叫失敗：{last_error}"
    except Exception as e:
        return None, f"Gemini SDK 尚未可用：{e}"


def detect_category(name):
    groups = {
        "保養美妝": ["洗面", "乳液", "精華", "面膜", "香水", "化妝", "保養"],
        "3C": ["手機", "耳機", "充電", "鍵盤", "滑鼠", "電腦", "平板"],
        "食品": ["芭樂", "零食", "餅乾", "水果", "茶", "咖啡", "食品"],
        "居家生活": ["清潔", "收納", "杯", "鍋", "家居", "居家"],
        "服飾": ["衣", "褲", "鞋", "帽", "包", "服飾"],
        "汽機車": ["汽車", "機車", "車用", "輪胎"],
    }
    for cat, words in groups.items():
        if any(w in name for w in words):
            return cat
    return "其他"


def local_analysis(name, category, price, points):
    return f"""商品名稱：{name}\n分類：{category}\n售價：{price}\n賣點：{points or '未提供'}\n\n分析：此商品應以圖片可確認資訊為主，未能確認的規格不可自行補寫。建議主打清楚、可信、易理解的購買理由。\n\n真實性規則：{TRUTH_RULE}"""


def local_shopee(name, category, price, points):
    return f"""【蝦皮商品標題】\n{name}｜{category}｜高轉換商品關鍵字\n\n【商品描述】\n{points or '請依商品圖片確認實際特色。'}\n\n【購買重點】\n1. 以實際商品圖片為準\n2. 未確認規格不自行承諾\n3. 下單前確認商品資訊\n\n【關鍵字】\n{name}、{category}、網購、熱門商品\n\n【價格】\nNT${price:,.0f}\n\n{TRUTH_RULE}"""


def local_tiktok(name, points):
    return f"""【TikTok 9:16 短影音腳本】\n商品：{name}\n\n0-3秒 Hook：\n「如果你正在找{name}，先看這裡！」\n\n3-8秒：商品近景與細節展示。\n\n8-15秒：依圖片能確認的特色逐一展示。\n\n15-20秒 CTA：\n「喜歡就收藏／查看商品頁，實際資訊以商品頁為準。」\n\n賣點參考：{points or '以實際圖片可確認內容為準。'}\n\n畫面比例：9:16\n禁止：改變商品外觀、品牌、包裝、Logo 或文字。"""


def local_jimeng(name, points, scene="高級商業產品攝影"):
    return f"""即夢 AI 2.5 商品影片 Prompt\n\n主體：使用上傳的「{name}」商品原圖作為唯一視覺來源。\n場景：{scene}。\n鏡頭：慢速電影感推近、微幅環繞、自然景深、乾淨高級商業攝影。\n內容：展示商品本身與圖片中可確認的細節。\n比例：9:16 直式短影音。\n\n硬性要求：{TRUTH_RULE}\n\n不可：重新設計商品、替換包裝、修改 Logo、改變品牌文字、增加不存在的配件、虛構規格或功效。\n賣點參考：{points or '只使用圖片可確認資訊。'}"""


def save_history(kind, payload):
    ensure_dirs()
    item = {"id": uuid.uuid4().hex[:10], "time": datetime.now().isoformat(timespec="seconds"), "kind": kind, "data": payload}
    path = HISTORY_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{item['id']}.json"
    save_json(path, item)


def ai_agent_task(task, product, selected_agents):
    name = product.get("name", "商品")
    category = product.get("category", "其他")
    price = product.get("price", 0)
    points = product.get("points", "")
    prompt = f"""你是黑金剛 AI 多 AI 電商總控中心的 Agent。\n任務：{task}\n商品：{name}\n分類：{category}\n售價：{price}\n賣點：{points}\n啟用 Agent：{', '.join(selected_agents)}\n\n{TRUTH_RULE}\n請以繁體中文輸出可直接使用的結果，未知資訊請明確標示。"""
    text, err = gemini_generate(prompt, product.get("image_bytes"))
    if text:
        return text, "Gemini"
    if "蝦皮" in task:
        return local_shopee(name, category, price, points), "Local"
    if "TikTok" in task or "短影音" in task:
        return local_tiktok(name, points), "Local"
    if "即夢" in task:
        return local_jimeng(name, points), "Local"
    return local_analysis(name, category, price, points), "Local"


def inject_css():
    st.markdown("""<style>
    .main-title{font-size:2rem;font-weight:800;margin-bottom:.2rem}.sub{opacity:.75}
    .agent-card{border:1px solid rgba(128,128,128,.25);padding:12px;border-radius:14px;margin:6px 0}
    .truth{padding:12px;border-radius:12px;background:rgba(255,180,0,.10);border:1px solid rgba(255,180,0,.35)}
    @media (max-width:700px){.main-title{font-size:1.45rem}}
    </style>""", unsafe_allow_html=True)


def login_page():
    st.title(APP_NAME)
    st.caption(APP_VERSION)
    with st.form("login"):
        u = st.text_input("帳號")
        p = st.text_input("密碼", type="password")
        if st.form_submit_button("登入", use_container_width=True):
            members = init_members()
            user = next((x for x in members if x.get("username") == u and x.get("password") == hash_password(p)), None)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("帳號或密碼錯誤")
    st.info("首次管理員：admin / admin123；登入後請自行修改程式中的管理方式或資料。")


def sidebar():
    st.sidebar.title("🖤 黑金剛 PRO")
    st.sidebar.caption(f"{APP_VERSION}｜Multi-AI Agent")
    page = st.sidebar.radio("功能中心", PAGES)
    st.sidebar.markdown("---")
    st.sidebar.caption(f"目前：{st.session_state.get('user', {}).get('username', 'Guest')}")
    if st.sidebar.button("登出", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    return page


def product_form():
    st.subheader("📷 商品資料")
    uploaded = st.file_uploader("從手機相簿／平板選擇商品圖片", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=False)
    name = st.text_input("商品名稱", value=st.session_state.get("last_name", ""))
    category = st.selectbox("商品分類", ["自動判斷", "保養美妝", "3C", "食品", "居家生活", "服飾", "汽機車", "其他"])
    price = st.number_input("售價", min_value=0.0, value=float(st.session_state.get("last_price", 999)))
    points = st.text_area("你已知的賣點／補充資訊")
    image = None
    image_bytes = None
    if uploaded:
        try:
            image, image_bytes = process_image(uploaded)
            st.image(image, caption="商品原圖", use_container_width=True)
        except Exception as e:
            st.error(str(e))
    final_category = detect_category(name) if category == "自動判斷" else category
    return {"name": name, "category": final_category, "price": price, "points": points, "image_bytes": image_bytes, "image": image}


def dashboard():
    st.markdown(f'<div class="main-title">{APP_NAME}</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub">一張商品圖 → 多 AI → 多 Agent → 電商內容工作流</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="truth">🛡️ <b>核心真實性規則</b><br>{TRUTH_RULE}</div>', unsafe_allow_html=True)
    products = load_json(PRODUCTS_FILE, [])
    orders = load_json(ORDERS_FILE, [])
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("商品", len(products)); c2.metric("訂單", len(orders)); c3.metric("AI Agents", len(AGENTS)); c4.metric("版本", APP_VERSION)
    st.subheader("⚡ 快速工作流")
    st.write("📷 上傳商品 → 🔍 分析 → 🛒 蝦皮 → 🎬 TikTok → 🧩 即夢 → 🖼️ 圖片 → 📊 利潤 → 🗂️ 素材庫")


def agent_center():
    st.header("🤖 AI Agent 多代理總控中心")
    st.caption("不是單一聊天機器人，而是可選 Agent 協作的電商工作流。")
    cols = st.columns(2)
    selected = []
    for i, (agent, desc) in enumerate(AGENTS.items()):
        with cols[i % 2]:
            if st.checkbox(agent, value=agent in ["🧠 總控 Agent", "🔍 商品視覺分析 Agent", "🧪 品質檢查 Agent"], key=f"agent_{i}"):
                selected.append(agent)
            st.caption(desc)
    st.markdown("---")
    task = st.text_area("告訴總控 Agent 你要完成什麼", value="把這個商品做成蝦皮商品頁＋TikTok 9:16 腳本＋即夢影片 Prompt＋AI 圖片 Prompt")
    product = product_form()
    if st.button("🚀 啟動多 Agent 工作流", type="primary", use_container_width=True):
        if not product["name"]:
            st.warning("請先輸入商品名稱")
            return
        with st.spinner("AI Agent 正在執行工作流…"):
            result, source = ai_agent_task(task, product, selected)
        st.success(f"完成｜來源：{source}")
        st.text_area("Agent 最終結果", result, height=520)
        save_history("AI Agent", {"task": task, "agents": selected, "product": {k:v for k,v in product.items() if k not in ["image", "image_bytes"]}, "result": result, "source": source})


def workspace():
    st.header("🛒 商品上架工作台")
    product = product_form()
    if st.button("✨ 一鍵產生完整商品包", type="primary", use_container_width=True):
        if not product["name"]:
            st.warning("請輸入商品名稱")
            return
        analysis, src1 = ai_agent_task("進行商品分析", product, ["🔍 商品視覺分析 Agent", "🛡️ 真實性 Agent"])
        shopee, src2 = ai_agent_task("建立蝦皮商品頁", product, ["🛒 蝦皮上架 Agent", "✍️ 文案 Agent", "🎯 SEO Agent"])
        tiktok, src3 = ai_agent_task("建立 TikTok 短影音", product, ["🎬 TikTok Agent", "🎥 短影音導演 Agent"])
        jimeng, src4 = ai_agent_task("建立即夢 AI 影片 Prompt", product, ["🧩 即夢 Agent", "🛡️ 真實性 Agent"])
        st.session_state["last_bundle"] = {"analysis":analysis,"shopee":shopee,"tiktok":tiktok,"jimeng":jimeng}
        for title, text in [("🔍 商品分析",analysis),("🛒 蝦皮",shopee),("🎬 TikTok",tiktok),("🧩 即夢",jimeng)]:
            st.subheader(title); st.text_area(title, text, height=280, key="out_"+title)
        save_history("商品完整包", st.session_state["last_bundle"])


def products_page():
    st.header("📦 商品管理")
    products = load_json(PRODUCTS_FILE, [])
    with st.form("product_add"):
        name = st.text_input("商品名稱")
        category = st.text_input("分類")
        price = st.number_input("售價", min_value=0.0)
        cost = st.number_input("成本", min_value=0.0)
        stock = st.number_input("庫存", min_value=0, step=1)
        if st.form_submit_button("新增商品"):
            if name:
                products.append({"id": uuid.uuid4().hex[:8], "name": name, "category": category, "price": price, "cost": cost, "stock": stock, "created": datetime.now().isoformat(timespec="seconds")})
                save_json(PRODUCTS_FILE, products); st.success("已新增"); st.rerun()
    if products:
        st.dataframe(products, use_container_width=True)
    else:
        st.info("尚無商品")


def orders_page():
    st.header("🧾 訂單管理")
    orders = load_json(ORDERS_FILE, [])
    with st.form("order_add"):
        product = st.text_input("商品")
        qty = st.number_input("數量", min_value=1, value=1)
        sale = st.number_input("單價", min_value=0.0)
        cost = st.number_input("單件成本", min_value=0.0)
        fee = st.number_input("平台／分潤費", min_value=0.0)
        ad = st.number_input("廣告費", min_value=0.0)
        other = st.number_input("其他成本", min_value=0.0)
        if st.form_submit_button("新增訂單"):
            revenue = qty * sale; total_cost = qty * cost + fee + ad + other; profit = revenue - total_cost
            orders.append({"date": str(date.today()), "product": product, "qty": qty, "revenue": revenue, "cost": total_cost, "profit": profit})
            save_json(ORDERS_FILE, orders); st.success("已新增")
    if orders: st.dataframe(orders, use_container_width=True)


def analytics_page():
    st.header("📊 數據分析")
    orders = load_json(ORDERS_FILE, [])
    revenue = sum(float(x.get("revenue",0)) for x in orders)
    cost = sum(float(x.get("cost",0)) for x in orders)
    profit = revenue - cost
    a,b,c = st.columns(3); a.metric("營收", f"NT${revenue:,.0f}"); b.metric("成本", f"NT${cost:,.0f}"); c.metric("利潤", f"NT${profit:,.0f}")
    if revenue: st.metric("利潤率", f"{profit/revenue*100:.1f}%")


def profit_page():
    st.header("💰 利潤／蝦皮分潤計算器")
    sale = st.number_input("售價", min_value=0.0, value=999.0)
    cost = st.number_input("商品成本", min_value=0.0, value=400.0)
    platform = st.number_input("平台費／分潤", min_value=0.0)
    ad = st.number_input("廣告費", min_value=0.0)
    shipping = st.number_input("運費／其他", min_value=0.0)
    profit = sale-cost-platform-ad-shipping
    st.metric("預估利潤", f"NT${profit:,.0f}")
    st.metric("利潤率", f"{profit/sale*100:.1f}%" if sale else "0%")


def tiktok_page():
    st.header("🎬 TikTok 短影音中心")
    product = product_form()
    if st.button("🎬 產生 TikTok 9:16 套件", type="primary", use_container_width=True):
        result, src = ai_agent_task("建立 TikTok 9:16 短影音腳本、Hook、分鏡、CTA", product, ["🎬 TikTok Agent", "🎥 短影音導演 Agent", "📱 社群 Agent"])
        st.text_area("TikTok 套件", result, height=550)
        save_history("TikTok", {"product": product["name"], "result": result, "source": src})


def image_page():
    st.header("🖼️ AI 圖片素材 Agent")
    product = product_form()
    target = st.selectbox("圖片用途", ["蝦皮 1:1 主圖", "商品介紹圖 1:1", "商品廣告圖 4:5", "TikTok 9:16"])
    if st.button("產生圖片 Prompt", type="primary", use_container_width=True):
        prompt = f"為商品『{product['name']}』產生{target}圖片生成 Prompt。只可使用商品圖片可確認資訊。{TRUTH_RULE}"
        text, err = gemini_generate(prompt, product.get("image_bytes"))
        if not text: text = f"{target} 商業攝影 Prompt：以商品原圖為唯一來源，保持商品完整一致，乾淨背景、高級商業攝影、清晰細節。\n{TRUTH_RULE}"
        st.text_area("圖片 Prompt", text, height=400)


def jimeng_page():
    st.header("🎥 即夢 AI 2.5 Agent")
    product = product_form()
    scene = st.text_input("影片風格／場景", "高級商業產品攝影棚")
    if st.button("🧩 產生即夢 Prompt", type="primary", use_container_width=True):
        prompt = f"產生即夢 AI 2.5 商品影片 Prompt。商品：{product['name']}；場景：{scene}；賣點：{product['points']}。比例9:16。{TRUTH_RULE}"
        text, err = gemini_generate(prompt, product.get("image_bytes"))
        if not text: text = local_jimeng(product["name"], product["points"], scene)
        st.text_area("即夢 AI 2.5 Prompt", text, height=500)
        st.info("本中心產生 Prompt，不直接呼叫影片生成 API。")


def materials_page():
    st.header("📚 AI 素材庫")
    files = sorted(HISTORY_DIR.glob("*.json"), reverse=True)
    if not files:
        st.info("尚無素材／歷史紀錄")
        return
    for f in files[:30]:
        data = load_json(f, {})
        with st.expander(f"{data.get('time','')}｜{data.get('kind','素材')}"):
            st.json(data.get("data", {}))


def history_page():
    st.header("🕘 歷史紀錄")
    files = sorted(HISTORY_DIR.glob("*.json"), reverse=True)
    for f in files[:50]:
        data = load_json(f, {})
        st.write(f"**{data.get('time','')}** — {data.get('kind','')}")


def members_page():
    st.header("👥 會員／管理中心")
    if st.session_state.get("user", {}).get("role") != "admin":
        st.warning("只有管理員可以使用")
        return
    members = init_members()
    st.dataframe(members, use_container_width=True)
    with st.form("member"):
        u = st.text_input("新會員帳號")
        p = st.text_input("新會員密碼", type="password")
        expires = st.date_input("到期日", value=date(2099,12,31))
        if st.form_submit_button("建立會員"):
            if u and p and not any(x.get("username") == u for x in members):
                members.append({"username":u,"password":hash_password(p),"role":"member","expires":str(expires)})
                save_json(MEMBERS_FILE,members); st.success("建立成功"); st.rerun()


def settings_page():
    st.header("⚙️ AI 設定")
    key = get_api_key()
    st.write("Gemini API 狀態：", "🟢 已設定" if key else "🟡 未設定／使用本地模式")
    st.caption("建議在 Streamlit Cloud → Settings → Secrets 設定 GEMINI_API_KEY。")
    st.write("模型優先順序：", " → ".join(GEMINI_MODELS))
    st.markdown("### 多 AI 架構")
    st.write("Gemini：主力視覺／文字 AI；DeepSeek、Ollama 等可在後續加入對應連接器。沒有 API 時仍可使用本地模板工作流。")


def main():
    ensure_dirs(); init_members()
    for k,v in {"logged_in":False,"user":None,"gemini_model":""}.items():
        if k not in st.session_state: st.session_state[k]=v
    st.set_page_config(page_title=APP_NAME, page_icon="🖤", layout="wide", initial_sidebar_state="expanded")
    inject_css()
    if not st.session_state.logged_in:
        login_page(); return
    page = sidebar()
    if page == "🏠 Dashboard": dashboard()
    elif page == "🤖 AI Agent 總控": agent_center()
    elif page == "🛒 商品上架工作台": workspace()
    elif page == "📦 商品管理": products_page()
    elif page == "🧾 訂單管理": orders_page()
    elif page == "📊 數據分析": analytics_page()
    elif page == "💰 利潤／蝦皮分潤": profit_page()
    elif page == "🎬 TikTok 短影音": tiktok_page()
    elif page == "🖼️ AI 圖片素材": image_page()
    elif page == "🎥 即夢 AI 2.5": jimeng_page()
    elif page == "📚 AI 素材庫": materials_page()
    elif page == "🕘 歷史紀錄": history_page()
    elif page == "👥 會員／管理中心": members_page()
    elif page == "⚙️ AI 設定": settings_page()


if __name__ == "__main__":
    main()
