import io
import json
import os
import re
import hashlib
from pathlib import Path
from datetime import datetime

import streamlit as st
from PIL import Image, ImageOps


# ============================================================
# AI 蝦皮自動化 2.5 PRO
# 單檔 Streamlit Cloud 版本
# ============================================================

APP_NAME = "AI 蝦皮自動化"
APP_VERSION = "2.5 PRO"

DATA_DIR = Path("data")
MEMBERS_FILE = DATA_DIR / "members.json"
PRODUCTS_FILE = DATA_DIR / "products.json"
HISTORY_FILE = DATA_DIR / "history.json"

MAX_IMAGE_SIZE = 1600
MAX_IMAGE_MB = 20

GEMINI_MODEL = "gemini-2.5-flash"


# ============================================================
# Streamlit 設定
# ============================================================

st.set_page_config(
    page_title=f"{APP_NAME} {APP_VERSION}",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background:
        radial-gradient(
            circle at 20% 0%,
            rgba(255, 90, 0, 0.10),
            transparent 28%
        ),
        radial-gradient(
            circle at 90% 20%,
            rgba(60, 120, 255, 0.07),
            transparent 25%
        ),
        #05080d;
    color: #f5f7fa;
}

#MainMenu,
footer {
    visibility: hidden;
}

section[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #0a1018,
            #070b11
        );
    border-right: 1px solid rgba(255,255,255,0.08);
}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}

.card {
    background:
        linear-gradient(
            145deg,
            #101923,
            #090f17
        );
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 14px;
}

.title {
    font-size: 25px;
    font-weight: 800;
}

.sub {
    color: #8995a4;
    font-size: 12px;
}

.section {
    font-size: 18px;
    font-weight: 800;
    margin: 14px 0 10px 0;
}

.badge {
    display: inline-block;
    margin-left: 8px;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 11px;
    color: #ff9d52;
    border: 1px solid #ff6a00;
    background: rgba(255,90,0,.10);
}

.metric {
    background:
        linear-gradient(
            145deg,
            #111a25,
            #0b1119
        );
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 13px;
    padding: 13px;
    min-height: 80px;
}

.metric-label {
    font-size: 11px;
    color: #8995a4;
}

.metric-value {
    font-size: 21px;
    font-weight: 800;
    margin-top: 4px;
}

.orange {
    color: #ff6a00;
}

.green {
    color: #50d890;
}

.blue {
    color: #4ab7ff;
}

.purple {
    color: #b28cff;
}

.workflow {
    display: flex;
    gap: 8px;
    align-items: center;
    background: #0b121b;
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 14px;
    padding: 12px;
    margin-bottom: 14px;
    overflow-x: auto;
}

.step {
    min-width: 120px;
    flex: 1;
    background: #101923;
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 11px;
    padding: 10px;
}

.step-icon {
    font-size: 22px;
}

.step-title {
    font-size: 13px;
    font-weight: 800;
}

.step-desc {
    font-size: 10px;
    color: #7e8a99;
}

.arrow {
    color: #ff6a00;
    font-size: 20px;
    font-weight: bold;
}

.check {
    color: #49d98c;
}

.tag {
    display: inline-block;
    padding: 5px 9px;
    margin: 3px;
    background: #172331;
    border: 1px solid #293a4b;
    border-radius: 7px;
    color: #b8c5d2;
    font-size: 11px;
}

.status-online {
    color: #50d890;
    font-weight: 800;
}

.status-offline {
    color: #ff9d52;
    font-weight: 800;
}

.stButton > button {
    border-radius: 8px !important;
    background: #111a24 !important;
    color: #fff !important;
    font-weight: 700 !important;
    border: 1px solid rgba(255,255,255,.12) !important;
}

.stButton > button:hover {
    border-color: #ff6a00 !important;
    color: #ff8b42 !important;
}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div {
    background: #0b121b !important;
    color: #fff !important;
    border-radius: 8px !important;
}

div[data-testid="stFileUploader"] {
    background: #0b121b;
    border-radius: 10px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 建立資料夾
# ============================================================

DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# JSON 工具
# ============================================================

def load_json(path, default):
    try:
        if not path.exists():
            return default

        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    except Exception:
        return default


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )
        return True

    except Exception:
        return False


# ============================================================
# Session State
# ============================================================

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

        "products": [],

        "members": [],

        "gemini_enabled": False,
        "gemini_model": GEMINI_MODEL,

        "last_analysis": "",
        "last_title": "",
        "last_description": "",
        "last_keywords": "",
        "last_tiktok": "",
        "last_jimeng": "",

        "login_user": "admin",

        "auto_save": True,
        "auto_analyze": True,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value

    st.session_state.history = load_json(
        HISTORY_FILE,
        st.session_state.history,
    )

    st.session_state.products = load_json(
        PRODUCTS_FILE,
        st.session_state.products,
    )

    st.session_state.members = load_json(
        MEMBERS_FILE,
        st.session_state.members,
    )


init_state()


# ============================================================
# 基本工具
# ============================================================

def clean_text(value):
    if value is None:
        return ""

    return str(value).strip()


def current_name():
    name = clean_text(
        st.session_state.get("product_name", "")
    )

    if name:
        return name

    return "玻尿酸保濕精華液"


def now_text():
    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# ============================================================
# 商品分類
# ============================================================

def detect_category(text):

    text = clean_text(text).lower()

    mapping = {
        "美妝保養": [
            "保養",
            "精華",
            "乳液",
            "面膜",
            "洗面",
            "化妝",
            "口紅",
            "防曬",
            "美容",
            "洗髮",
        ],
        "3C 電子": [
            "手機",
            "耳機",
            "充電",
            "電腦",
            "滑鼠",
            "鍵盤",
            "平板",
            "3c",
            "usb",
        ],
        "居家生活": [
            "收納",
            "清潔",
            "家用",
            "居家",
            "廚房",
            "水壺",
            "杯",
            "用品",
        ],
        "服飾鞋包": [
            "衣",
            "褲",
            "鞋",
            "包",
            "帽",
            "外套",
            "襪",
        ],
        "食品飲料": [
            "食品",
            "零食",
            "餅乾",
            "飲料",
            "咖啡",
            "茶",
            "糖",
        ],
        "汽機車": [
            "汽車",
            "機車",
            "車用",
            "汽機車",
            "輪胎",
            "行車",
        ],
    }

    for category, keywords in mapping.items():

        for keyword in keywords:

            if keyword.lower() in text:
                return category

    return "其他"


# ============================================================
# 商品資料
# ============================================================

def get_product_data():

    return {
        "商品名稱": current_name(),
        "商品分類": st.session_state.category,
        "商品價格": st.session_state.price,
        "商品庫存": st.session_state.stock,
        "商品狀態": st.session_state.condition,
        "商品賣點": st.session_state.selling_points,
        "圖片數量": len(st.session_state.images),
    }


# ============================================================
# AI 蝦皮核心指令碼
# ============================================================

SHOPEE_AI_SYSTEM_PROMPT = """
你是「AI 蝦皮自動化 2.5 PRO」的核心電商 AI。

你的工作是協助賣家建立：
1. 蝦皮商品標題
2. 商品描述
3. 商品賣點
4. 商品關鍵字
5. TikTok 短影音文案
6. 即夢 AI 2.5 商品影片 Prompt

核心規則：

【商品真實性】
只能使用使用者提供的商品資料與商品圖片。
不得虛構不存在的品牌。
不得虛構規格。
不得虛構容量。
不得虛構功效。
不得虛構認證。
不得虛構成分。
不得虛構價格。
不得虛構庫存。

【圖片規則】
如果有商品圖片：
圖片中的商品是唯一主要視覺來源。
必須盡量維持：
- 原始商品形狀
- 原始包裝
- 原始顏色
- 原始材質
- 原始 Logo
- 原始標籤
- 原始可見文字

不得重新設計商品。
不得更改品牌。
不得生成假的 Logo。
不得加入不存在的包裝文字。
不得改變商品外觀。

【蝦皮標題】
標題要清楚。
避免無意義關鍵字堆疊。
避免虛假宣稱。
避免誇張醫療效果。
避免保證性效果。

【商品描述】
內容要適合電商商品頁。
結構清楚。
可以使用 Emoji。
不得虛構產品資訊。

【TikTok】
使用 9:16 短影音邏輯。
前 3 秒要有吸引力。
內容以商品展示、使用情境、特色為主。

【即夢 AI 2.5】
影片為 9:16。
商品必須維持原貌。
以商品圖片為唯一產品視覺來源。
推薦使用：
- cinematic product commercial
- slow push-in
- subtle orbit
- premium lighting
- clean background

不得：
- 改品牌
- 改 Logo
- 改包裝
- 改文字
- 改產品形狀
- 虛構產品
"""


# ============================================================
# 本地 AI 內容生成
# ============================================================

def local_analysis():

    product = get_product_data()

    name = product["商品名稱"]
    category = product["商品分類"]
    price = product["商品價格"]
    stock = product["商品庫存"]
    points = product["商品賣點"]

    if not points:
        points = "未提供額外賣點，請以商品圖片與基本資料為準。"

    return f"""
【商品分析】

商品名稱：
{name}

商品分類：
{category}

商品價格：
NT${price}

目前庫存：
{stock}

商品狀態：
{st.session_state.condition}

使用者提供的賣點：
{points}

圖片數量：
{len(st.session_state.images)} 張

【AI 分析原則】

目前系統採用安全模式。
未提供的商品規格不自行補充。
商品圖片如果存在，應以圖片中的實際資訊為準。

建議銷售方向：
1. 清楚介紹商品用途
2. 強調使用者實際提供的賣點
3. 使用簡潔電商語言
4. 避免誇張與虛假功效
5. 避免虛構品牌與規格
""".strip()


def local_title():

    name = current_name()

    return (
        f"{name}｜日常使用｜實用推薦｜蝦皮熱賣商品"
    )


def local_description():

    name = current_name()

    points = clean_text(
        st.session_state.selling_points
    )

    if not points:
        points = "商品特色請依實際商品資訊確認"

    return f"""
🛍️ {name}

✨ 商品特色
• {points}

📦 商品資訊
• 商品名稱：{name}
• 商品分類：{st.session_state.category}
• 商品狀態：{st.session_state.condition}
• 商品庫存：{st.session_state.stock}

💡 購買提醒
商品實際內容、包裝、規格與標示，
請以收到的實體商品及賣場資訊為準。

🚚 出貨
依賣場選擇的物流方式出貨。

📌 注意
圖片與文字僅作為商品展示，
實際商品請以商品頁資訊為準。
""".strip()


def local_keywords():

    name = current_name()

    base = [
        "蝦皮",
        "網路購物",
        "熱賣",
        "推薦",
        st.session_state.category,
    ]

    words = re.findall(
        r"[\u4e00-\u9fffA-Za-z0-9]+",
        name,
    )

    base.extend(words)

    unique = []

    for item in base:

        item = clean_text(item)

        if item and item not in unique:
            unique.append(item)

    return ",".join(unique[:20])


def local_tiktok():

    name = current_name()

    return f"""
🎬 TikTok 9:16 短影音腳本

【0-3 秒｜Hook】
「還在找 {name} 嗎？」

【3-7 秒｜商品登場】
鏡頭快速帶到商品本體，
以商品原始外觀作為主要視覺。

【7-12 秒｜商品特色】
展示商品外觀與使用情境，
搭配簡潔文字說明商品賣點。

【12-17 秒｜細節】
特寫商品包裝、材質與細節。

【17-20 秒｜CTA】
「想了解更多商品資訊，
可以到賣場看看！」

畫面比例：9:16
風格：高質感商品短影音
注意：不得改變商品原始外觀。
""".strip()


def local_jimeng():

    name = current_name()

    return f"""
即夢 AI 2.5 商品影片 Prompt

9:16 vertical premium commercial product video.

Main product:
{name}

IMPORTANT PRODUCT PRESERVATION RULES:

Use the uploaded product image as the ONLY visual source for the product.

Preserve the original:
- product shape
- packaging
- logo
- label
- colors
- material
- visible text
- proportions
- brand identity

Do not redesign the product.
Do not invent a logo.
Do not invent text.
Do not change the packaging.
Do not change the product shape.
Do not create a different product.

Camera:
slow cinematic push-in,
subtle orbit movement,
smooth camera motion,
premium commercial photography.

Lighting:
soft studio lighting,
clean premium lighting,
realistic reflections,
natural shadows.

Background:
minimal luxury commercial environment,
clean,
simple,
uncluttered.

Video:
high-end product advertisement,
realistic,
photorealistic,
professional commercial style.

Aspect ratio:
9:16 vertical.

Negative instructions:
no fake logo,
no fake label,
no packaging redesign,
no distorted product,
no extra product,
no incorrect text,
no brand replacement,
no unrealistic deformation.
""".strip()


# ============================================================
# Gemini
# ============================================================

def get_gemini_key():

    try:

        key = st.secrets.get(
            "GEMINI_API_KEY",
            "",
        )

        if key:
            return clean_text(key)

    except Exception:
        pass

    return clean_text(
        os.environ.get(
            "GEMINI_API_KEY",
            "",
        )
    )


def get_gemini_client():

    key = get_gemini_key()

    if not key:
        return None

    try:

        from google import genai

        return genai.Client(
            api_key=key
        )

    except Exception:

        return None


def gemini_available():

    return get_gemini_client() is not None


def build_gemini_prompt():

    product = get_product_data()

    return f"""
{SHOPEE_AI_SYSTEM_PROMPT}

請根據以下商品資料進行電商內容生成。

商品資料：
{json.dumps(product, ensure_ascii=False, indent=2)}

請輸出：

【商品分析】
說明商品資訊與可使用的行銷方向。

【蝦皮標題】
提供 3 個候選標題。

【商品描述】
產生完整商品描述。

【關鍵字】
提供適合搜尋的關鍵字。

【TikTok】
提供 20 秒左右的 9:16 短影音腳本。

【即夢 AI 2.5】
提供商品影片 Prompt。

重要：
所有沒有提供的資訊不要自行虛構。
""".strip()


def call_gemini():

    client = get_gemini_client()

    if client is None:
        return None, "目前沒有可用的 Gemini API Key。"

    prompt = build_gemini_prompt()

    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )

        text = getattr(
            response,
            "text",
            None,
        )

        if not text:
            return None, "Gemini 沒有返回文字內容。"

        return text.strip(), ""

    except Exception as exc:

        return None, f"Gemini 呼叫失敗：{exc}"


# ============================================================
# 儲存歷史
# ============================================================

def save_history(action):

    item = {
        "時間": now_text(),
        "商品": current_name(),
        "操作": action,
    }

    history = load_json(
        HISTORY_FILE,
        [],
    )

    history.insert(0, item)

    history = history[:500]

    save_json(
        HISTORY_FILE,
        history,
    )

    st.session_state.history = history


# ============================================================
# 儲存商品
# ============================================================

def save_product():

    product = {
        "id": hashlib.md5(
            f"{current_name()}-{now_text()}".encode(
                "utf-8"
            )
        ).hexdigest()[:12],

        "時間": now_text(),
        "商品名稱": current_name(),
        "分類": st.session_state.category,
        "價格": st.session_state.price,
        "庫存": st.session_state.stock,
        "狀態": st.session_state.condition,
        "賣點": st.session_state.selling_points,
        "商品狀態": "草稿",
    }

    products = load_json(
        PRODUCTS_FILE,
        [],
    )

    products.insert(
        0,
        product,
    )

    products = products[:500]

    save_json(
        PRODUCTS_FILE,
        products,
    )

    st.session_state.products = products


# ============================================================
# 執行工作流
# ============================================================

def execute_workflow():

    if not clean_text(
        st.session_state.product_name
    ):

        st.session_state.product_name = (
            "玻尿酸保濕精華液"
        )

    st.session_state.last_analysis = (
        local_analysis()
    )

    st.session_state.last_title = (
        local_title()
    )

    st.session_state.last_description = (
        local_description()
    )

    st.session_state.last_keywords = (
        local_keywords()
    )

    st.session_state.last_tiktok = (
        local_tiktok()
    )

    st.session_state.last_jimeng = (
        local_jimeng()
    )

    # 如果 Gemini 可用，嘗試取得 AI 結果
    if gemini_available():

        result, error = call_gemini()

        if result:

            st.session_state.last_analysis = (
                result
            )

            st.session_state.gemini_enabled = True

        else:

            st.session_state.gemini_enabled = False

    else:

        st.session_state.gemini_enabled = False

    st.session_state.generated = True

    save_product()

    save_history(
        "執行 AI 商品工作流"
    )


# ============================================================
# Sidebar
# ============================================================

def sidebar():

    with st.sidebar:

        st.markdown(
            """
<div class="card">
    <div style="font-size:19px;font-weight:800">
        🛍️ AI 蝦皮自動化
    </div>
    <div class="sub">
        AI 智能生成・商品自動化工作台
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

        menus = [
            ("🏠", "Dashboard"),
            ("🛍️", "商品上架工作台"),
            ("📦", "商品管理"),
            ("🧾", "訂單管理"),
            ("📊", "數據分析"),
            ("🖼️", "AI 素材庫"),
            ("🕘", "歷史紀錄"),
            ("🎵", "TikTok 短影音"),
            ("💰", "蝦皮分潤管理"),
        ]

        for icon, name in menus:

            if st.button(
                f"{icon}  {name}",
                key=f"nav_{name}",
                use_container_width=True,
            ):

                st.session_state.page = name
                st.rerun()

        st.markdown("---")

        system_menus = [
            ("👤", "會員管理"),
            ("🛡️", "管理員中心"),
            ("⚙️", "系統設定"),
            ("🔑", "API 設定"),
            ("📚", "使用教學"),
        ]

        for icon, name in system_menus:

            if st.button(
                f"{icon}  {name}",
                key=f"sys_{name}",
                use_container_width=True,
            ):

                st.session_state.page = name
                st.rerun()

        st.markdown(
            """
<div class="card">
    <b style="color:#ff8a3d">
        👑 PRO 會員
    </b>
    <br>
    <span class="check">✓</span> AI 商品工作流
    <br>
    <span class="check">✓</span> 商品圖片
    <br>
    <span class="check">✓</span> 蝦皮文案
    <br>
    <span class="check">✓</span> TikTok 9:16
    <br>
    <span class="check">✓</span> 即夢 Prompt
    <br>
    <span class="check">✓</span> 歷史紀錄
</div>
""",
            unsafe_allow_html=True,
        )


# ============================================================
# Header
# ============================================================

def header():

    gemini_status = (
        "Gemini AI"
        if gemini_available()
        else "離線模式"
    )

    st.markdown(
        f"""
<div class="card">
    <div class="title">
        🛍️ AI 蝦皮自動化
        <span class="badge">
            {APP_VERSION}
        </span>
    </div>

    <div class="sub">
        AI 智能生成・商品工作流・蝦皮上架準備
        ｜目前：{gemini_status}
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


# ==================
