import json
import os
import hashlib
from datetime import datetime, date, timedelta
import streamlit as st

# ============================================================
# 常數與設定
# ============================================================

APP_NAME = "黑金剛 AI"
APP_VERSION = "2.5"
MEMBERS_FILE = "members.json"
HISTORY_FILE = "history.json"

# 即夢 AI 2.5 核心 Prompt 指令規範
JIMENG_25_CORE_RULES = """
你是一位頂級 AI 視覺導演與即夢 AI 2.5 (Jimeng AI 2.5) 提示詞工程專家。
請根據輸入的商品資訊，產出符合即夢 AI 2.5 最強畫質與動態表現的分鏡與 Prompt。

格式要求：
1. 畫面比例：9:16（適合 TikTok / Reels / Shorts）。
2. 運鏡指令：明確包含 Pan, Tilt, Zoom, Orbit 等專業動向。
3. 視覺風格：電影級光影、超高畫質 (8k resolution, photorealistic, cinematic lighting)。
4. 分鏡架構：包含 3~5 個關鍵鏡頭 (Shot Breakdown)。
"""

# ============================================================
# 資料存取與輔助函式
# ============================================================

def hash_password(password: str) -> str:
    """使用 SHA-256 雜湊密碼"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    """驗證密碼"""
    return hash_password(password) == hashed_password

def load_members() -> dict:
    """載入會員資料"""
    if os.path.exists(MEMBERS_FILE):
        try:
            with open(MEMBERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # 預設管理員帳號 (admin / admin123)
    default_admin = {
        "admin": {
            "username": "admin",
            "password": hash_password("admin123"),
            "role": "admin",
            "expires": "永久",
            "active": True,
            "created_at": datetime.now().isoformat(),
        }
    }
    save_members(default_admin)
    return default_admin

def save_members(members: dict):
    """保存會員資料"""
    with open(MEMBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(members, f, ensure_ascii=False, indent=2)

def member_is_active(member: dict) -> bool:
    """檢查會員狀態與效期"""
    if not member.get("active", True):
        return False
    expires = member.get("expires")
    if expires == "永久":
        return True
    try:
        exp_date = date.fromisoformat(expires)
        return date.today() <= exp_date
    except Exception:
        return False

def days_remaining(member: dict) -> int:
    """計算剩餘天數"""
    expires = member.get("expires")
    if expires == "永久":
        return 9999
    try:
        exp_date = date.fromisoformat(expires)
        delta = (exp_date - date.today()).days
        return max(0, delta)
    except Exception:
        return 0

def load_history() -> list:
    """載入歷史紀錄"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(record: dict):
    """保存歷史紀錄"""
    records = load_history()
    records.insert(0, record)  # 最新紀錄排前面
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

def detect_product_category(name: str) -> str:
    """簡易分類檢測"""
    food_keywords = ["甘草", "芭樂", "零食", "餅乾", "特產", "美食", "水果"]
    if any(k in name for k in food_keywords):
        return "食品"
    return "通用商品"

def process_image(uploaded_file):
    """處理上傳圖片"""
    from PIL import Image
    import io
    image = Image.open(uploaded_file)
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return image, buf.getvalue()

# ============================================================
# AI 邏輯生成 (預設模擬邏輯，可自行對接 SDK)
# ============================================================

def analyze_product(name, category, price, selling_points):
    return f"【商品分析報告】\n- 名稱：{name}\n- 分類：{category}\n- 定價：NT$ {price}\n- 核心訴求：{selling_points or '高CP值、優質選品'}\n- 受眾分析：喜好便利、注重CP值與生活品質的族群。"

def generate_shopee_copy(name, category, price, selling_points):
    return f"🔥【爆款推薦】{name} 🔥\n\n✨ 必買亮點：\n{selling_points or '精選品質，超值優惠！'}\n\n💰 限時優惠價：NT$ {price}\n📦 全館現貨直送，數量有限搶完為止！\n\n#蝦皮好物 #{category} #{name}"

def generate_tiktok_copy(name, selling_points):
    return f"🎬 TikTok 15秒短影音腳本：{name}\n\n[00:00-00:03 痛點黃金前3秒]\n畫面：近鏡頭衝擊\n台詞：還在找高品質的{name}嗎？看這支影片就夠了！\n\n[00:03-00:10 賣點展示]\n畫面：動態使用特寫\n台詞：{selling_points or '這個細節處理得太棒了，CP值直接拉滿！'}\n\n[00:10-00:15 強效促導]\n畫面：點擊下方小黃車\n台詞：點擊左下角，現在下單享有獨家優惠！"

def generate_seedance_prompt(name, category, price, selling_points):
    return f"""{JIMENG_25_CORE_RULES}

[即夢 AI 2.5 專用指令]
Subject: {name} ({category})
Style: Photorealistic 8k, cinematic product lighting, commercial product display.
Camera Movement: Slow Orbit & Push-in.
Key Highlights: {selling_points or 'Sleek design, premium texture'}

Prompt:
Professional studio product shot of {name}, high-end commercial aesthetic, 8k resolution, sharp focus, vibrant color palette, dynamic lighting, cinematic depth of field, 9:16 aspect ratio --v 2.5
"""

def build_gemini_prompt(product_data, selected, mode):
    return f"請分析這張圖片，結合商品資料：{json.dumps(product_data, ensure_ascii=False)}，產出視覺行銷建言。"

def call_gemini(prompt, image_bytes, mime_type):
    return f"【Gemini 視覺視覺分析】\n這張商品圖片構圖清晰，光影對比良好。建議可在畫面邊角加入文字標籤增強點擊率。"

# ============================================================
# UI 介面設定與 Session 初始化
# ============================================================

def inject_css():
    st.markdown(
        """
        <style>
        .hero {
            background: linear-gradient(135deg, #1e1e1e 0%, #3a3a3a 100%);
            padding: 2rem;
            border-radius: 12px;
            color: white;
            margin-bottom: 2rem;
            text-align: center;
        }
        .hero h1 { color: #f39c12; margin-bottom: 0.5rem; }
        .pro {
            background-color: #f39c12;
            color: black;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.8rem;
        }
        .card {
            background: #262626;
            padding: 1rem;
            border-radius: 8px;
            color: #ddd;
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def init_session():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "role" not in st.session_state:
        st.session_state.role = ""
    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = ""
    if "generated_shopee" not in st.session_state:
        st.session_state.generated_shopee = ""
    if "generated_tiktok" not in st.session_state:
        st.session_state.generated_tiktok = ""
    if "generated_jimeng" not in st.session_state:
        st.session_state.generated_jimeng = ""
    if "gemini_error" not in st.session_state:
        st.session_state.gemini_error = ""

# ============================================================
# 登入頁面
# ============================================================

def login_page():
    st.markdown(
        f"""
        <div class="hero">
            <h1>⚫ {APP_NAME}</h1>
            <span class="pro">PRO</span>
            <p>AI 商品營運 × 蝦皮 × TikTok × 即夢 AI 2.5</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.subheader("登入系統")

        username = st.text_input("帳號", key="login_username")
        password = st.text_input("密碼", type="password", key="login_password")

        if st.button("登入", use_container_width=True, type="primary", key="login_submit_btn"):
            members = load_members()
            member = members.get(username)

            if member and verify_password(password, member.get("password", "")):
                if not member_is_active(member):
                    st.error("會員已過期或停用。")
                    return

                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = member.get("role", "member")
                st.session_state.page = "Dashboard"
                st.rerun()
            else:
                st.error("帳號或密碼錯誤。")

        st.info("預設管理員：admin / admin123")

# ============================================================
# Sidebar 側邊欄
# ============================================================

def sidebar():
    members = load_members()
    current = members.get(st.session_state.username, {})

    with st.sidebar:
        st.title("⚫ 黑金剛")
        st.caption(f"{APP_NAME} v{APP_VERSION}")
        st.divider()

        st.write(f"👤 {st.session_state.username}")

        if current.get("expires") == "永久":
            st.success("♾️ 永久會員")
        else:
            st.info(f"剩餘 {days_remaining(current)} 天")

        st.divider()

        pages = [
            "Dashboard",
            "商品上架工作台",
            "商品管理",
            "訂單管理",
            "數據分析",
            "AI素材庫",
            "歷史紀錄",
            "TikTok短影音",
            "蝦皮分潤管理",
        ]

        if st.session_state.role == "admin":
            pages.append("管理員中心")

        current_page = st.session_state.page

        selected = st.radio(
            "功能選單",
            pages,
            index=pages.index(current_page) if current_page in pages else 0,
            key="sidebar_menu_radio",
        )

        st.session_state.page = selected
        st.divider()

        if st.button("登出", use_container_width=True, key="sidebar_logout_btn"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = ""
            st.rerun()

# ============================================================
# Dashboard 儀表板
# ============================================================

def dashboard():
    st.title("Dashboard")

    st.markdown(
        f"""
        <div class="hero">
            <h1>黑金剛 AI 總控中心</h1>
            <p>商品 → AI分析 → 蝦皮 → TikTok → 即夢 AI 2.5</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    records = load_history()
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("歷史商品", len(records))
    c2.metric("AI系統", "Ready")
    c3.metric("即夢 Prompt", "2.5")
    c4.metric("影片比例", "9:16")

# ============================================================
# 商品上架工作台
# ============================================================

def product_workspace():
    st.title("📦 商品上架工作台")

    st.markdown(
        """
        <div class="card">
        商品圖片 → AI分析 → 蝦皮文案 → TikTok → 即夢 AI 2.5
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        product_name = st.text_input("商品名稱", placeholder="例如：甘草芭樂", key="workspace_product_name")
        category = st.text_input("商品分類", placeholder="食品", key="workspace_category")
        price = st.number_input("商品價格", min_value=0, value=999, step=1, key="workspace_price")
        selling_points = st.text_area("商品賣點", placeholder="輸入你知道的商品賣點", height=120, key="workspace_selling_points")

    with col2:
        uploaded = st.file_uploader("商品圖片", type=["jpg", "jpeg", "png", "webp"], key="workspace_uploader")

        image = None
        image_bytes = None

        if uploaded:
            try:
                image, image_bytes = process_image(uploaded)
                st.image(image, caption="商品原圖", use_container_width=True)
            except Exception as e:
                st.error(str(e))

    st.divider()
    st.subheader("AI 產生項目")

    selected = st.multiselect(
        "選擇要產生的內容",
        ["商品分析", "蝦皮商品文案", "TikTok短影音", "即夢 AI 2.5 Prompt", "Gemini圖片分析"],
        default=["商品分析", "蝦皮商品文案", "TikTok短影音", "即夢 AI 2.5 Prompt"],
        key="workspace_selected_items",
    )

    generate = st.button("🚀 開始生成", type="primary", use_container_width=True, key="workspace_generate_btn")

    if generate:
        if not product_name:
            st.warning("請先輸入商品名稱。")
            return

        # 重置舊狀態，防止數據殘留
        st.session_state.analysis_result = ""
        st.session_state.generated_shopee = ""
        st.session_state.generated_tiktok = ""
        st.session_state.generated_jimeng = ""
        st.session_state.gemini_error = ""

        detected_category = category or detect_product_category(product_name)

        product_data = {
            "商品名稱": product_name,
            "商品分類": detected_category,
            "價格": price,
            "商品賣點": selling_points,
        }

        st.session_state.last_product_name = product_name

        if "商品分析" in selected:
            st.session_state.analysis_result = analyze_product(
                product_name, detected_category, price, selling_points
            )

        if "蝦皮商品文案" in selected:
            st.session_state.generated_shopee = generate_shopee_copy(
                product_name, detected_category, price, selling_points
            )

        if "TikTok短影音" in selected:
            st.session_state.generated_tiktok = generate_tiktok_copy(
                product_name, selling_points
            )

        if "即夢 AI 2.5 Prompt" in selected:
            st.session_state.generated_jimeng = generate_seedance_prompt(
                product_name, detected_category, price, selling_points
            )

        if "Gemini圖片分析" in selected and image_bytes:
            try:
                prompt = build_gemini_prompt(product_data, selected, "蝦皮 + TikTok + 即夢 AI 2.5")
                gemini_result = call_gemini(prompt, image_bytes, "image/jpeg")

                # 避免無條件覆蓋商品分析結果，採取累加
                if st.session_state.analysis_result:
                    st.session_state.analysis_result += f"\n\n--------------------\n{gemini_result}"
                else:
                    st.session_state.analysis_result = gemini_result
            except Exception as e:
                st.session_state.gemini_error = str(e)

        history_data = {
            "created_at": datetime.now().isoformat(),
            "username": st.session_state.username,
            "product": product_data,
            "selected": selected,
            "shopee": st.session_state.generated_shopee,
            "tiktok": st.session_state.generated_tiktok,
            "jimeng": st.session_state.generated_jimeng,
        }

        save_history(history_data)
        st.success("生成完成，已保存到歷史紀錄。")

    if st.session_state.analysis_result:
        st.subheader("🧠 商品分析")
        st.text_area("AI分析結果", st.session_state.analysis_result, height=300, key="workspace_analysis_result")

    if st.session_state.generated_shopee:
        st.subheader("🛒 蝦皮商品文案")
        st.text_area("蝦皮文案", st.session_state.generated_shopee, height=350, key="workspace_shopee_result")

    if st.session_state.generated_tiktok:
        st.subheader("🎬 TikTok短影音")
        st.text_area("TikTok內容", st.session_state.generated_tiktok, height=350, key="workspace_tiktok_result")

    if st.session_state.generated_jimeng:
        st.subheader("🎥 即夢 AI 2.5 Prompt")
        st.text_area("即夢 Prompt", st.session_state.generated_jimeng, height=700, key="workspace_jimeng_result")

        st.download_button(
            "⬇️ 下載即夢 Prompt",
            data=st.session_state.generated_jimeng,
            file_name="jimeng_2.5_prompt.txt",
            mime="text/plain",
            use_container_width=True,
            key="workspace_download_jimeng",
        )

    if st.session_state.gemini_error:
        st.error(st.session_state.gemini_error)

# ============================================================
# 其他子頁面
# ============================================================

def product_management():
    st.title("📦 商品管理")
    records = load_history()
    if not records:
        st.info("目前沒有商品紀錄。")
        return

    for record in records:
        product = record.get("product", {})
        with st.expander(f"{product.get('商品名稱', '未知商品')} ｜ {record.get('created_at', '')}"):
            st.json(product)

def order_management():
    st.title("📋 訂單管理")
    st.info("目前為管理介面。真正蝦皮訂單同步需要接蝦皮官方 API。")

def analytics():
    st.title("📊 數據分析")
    records = load_history()
    st.metric("目前歷史紀錄", len(records))

    if records:
        categories = {}
        for record in records:
            product = record.get("product", {})
            category = product.get("商品分類", "其他")
            categories[category] = categories.get(category, 0) + 1

        st.subheader("商品分類統計")
        st.bar_chart(categories)

def ai_materials():
    st.title("🧠 AI素材庫")
    st.write("集中管理商品分析、蝦皮文案、TikTok腳本與即夢 AI 2.5 Prompt。")
    records = load_history()
    for record in records[:20]:
        product = record.get("product", {})
        st.write(f"📦 {product.get('商品名稱', '未知')}")

def history_page():
    st.title("🕘 歷史紀錄")
    records = load_history()
    if not records:
        st.info("尚無歷史紀錄。")
        return

    for index, record in enumerate(records):
        product = record.get("product", {})
        with st.expander(product.get("商品名稱", "未知商品")):
            st.write(record.get("created_at", ""))

            if record.get("shopee"):
                st.subheader("蝦皮")
                st.text_area("Shopee", record["shopee"], height=200, key=f"history_shopee_{index}")

            if record.get("tiktok"):
                st.subheader("TikTok")
                st.text_area("TikTok", record["tiktok"], height=200, key=f"history_tiktok_{index}")

            if record.get("jimeng"):
                st.subheader("即夢 AI 2.5")
                st.text_area("Jimeng", record["jimeng"], height=350, key=f"history_jimeng_{index}")

def tiktok_page():
    st.title("🎬 TikTok 短影音中心")
    product_name = st.text_input("商品名稱", key="tiktok_product_name")
    selling_points = st.text_area("商品賣點", key="tiktok_selling_points")

    if st.button("生成 TikTok 腳本", type="primary", key="tiktok_generate_btn"):
        if not product_name:
            st.warning("請輸入商品名稱。")
            return

        result = generate_tiktok_copy(product_name, selling_points)
        st.text_area("TikTok腳本", result, height=450, key="tiktok_result")

def affiliate_page():
    st.title("💰 蝦皮分潤管理")
    price = st.number_input("商品售價", min_value=0.0, value=999.0, key="affiliate_price")
    commission = st.number_input("預估分潤比例 %", min_value=0.0, max_value=100.0, value=5.0, key="affiliate_commission")
    result = price * commission / 100
    st.metric("預估分潤", f"NT$ {result:,.0f}")

def admin_center():
    if st.session_state.role != "admin":
        st.error("沒有管理員權限。")
        return

    st.title("👑 管理員中心")
    members = load_members()

    st.subheader("會員管理")
    for username, member in members.items():
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.write(username)
        with col2:
            st.write("♾️ 永久" if member.get("expires") == "永久" else member.get("expires", ""))
        with col3:
            st.write("啟用" if member.get("active", True) else "停用")

    st.divider()
    st.subheader("新增會員")

    new_username = st.text_input("新會員帳號", key="new_member_username")
    new_password = st.text_input("新會員密碼", type="password", key="new_member_password")
    permanent = st.checkbox("永久會員", value=True, key="new_member_permanent")
    days = st.number_input("會員天數", min_value=1, value=30, key="new_member_days")

    if st.button("建立會員", type="primary", key="create_member_btn"):
        if not new_username or not new_password:
            st.warning("帳號與密碼不可為空。")
        elif new_username in members:
            st.error("會員已存在。")
        else:
            expires = "永久" if permanent else (date.today() + timedelta(days=int(days))).isoformat()
            members[new_username] = {
                "username": new_username,
                "password": hash_password(new_password),
                "role": "member",
                "expires": expires,
                "active": True,
                "created_at": datetime.now().isoformat(),
   
