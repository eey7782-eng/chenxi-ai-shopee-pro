# ============================================================
# AI 蝦皮自動化 2.5 PRO
# 完整單檔 Streamlit 版本
#
# 功能：
# 1. Gemini API
# 2. Gemini 商品圖片分析
# 3. AI 商品標題
# 4. AI 商品描述
# 5. SEO 關鍵字
# 6. 商品賣點
# 7. TikTok 9:16
# 8. 即夢 AI 2.5 Prompt
# 9. 蝦皮商品預覽
# 10. 歷史紀錄
# 11. API 設定
# 12. 無 API 也可啟動
# ============================================================

import io
import os
import re
import json
from datetime import datetime

import streamlit as st
from PIL import Image


# ============================================================
# APP 基本設定
# ============================================================

APP_NAME = "AI 蝦皮自動化"
APP_VERSION = "2.5 PRO"

DEFAULT_PRODUCT = "玻尿酸保濕精華液"

DEFAULT_CATEGORY = "美妝保養"

DEFAULT_PRICE = 499

DEFAULT_STOCK = 100


# ============================================================
# Gemini 模型
# ============================================================

# 使用目前 SDK 可用的 Gemini Flash 模型。
# 如果第一個模型失敗，程式會自動嘗試後面的模型。
GEMINI_MODELS = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-2.5-flash",
]


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
            rgba(255,90,0,.10),
            transparent 28%
        ),
        #05080d;
    color: #f5f7fa;
}

#MainMenu {
    visibility: hidden;
}

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
    border-right:
        1px solid rgba(255,255,255,.08);
}

.card {
    background:
        linear-gradient(
            145deg,
            #101923,
            #090f17
        );
    border:
        1px solid rgba(255,255,255,.08);
    border-radius: 14px;
    padding: 18px;
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
    padding: 4px 9px;
    border-radius: 6px;
    font-size: 11px;
    color: #ff9d52;
    border: 1px solid #ff6a00;
    background: rgba(255,90,0,.1);
}

.metric {
    background:
        linear-gradient(
            145deg,
            #111a25,
            #0b1119
        );
    border:
        1px solid rgba(255,255,255,.07);
    border-radius: 13px;
    padding: 14px;
    min-height: 82px;
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
    border:
        1px solid rgba(255,255,255,.07);
    border-radius: 14px;
    padding: 12px;
    margin-bottom: 14px;
    overflow-x: auto;
}

.step {
    min-width: 125px;
    flex: 1;
    background: #101923;
    border:
        1px solid rgba(255,255,255,.08);
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
    border:
        1px solid #293a4b;
    border-radius: 7px;
    color: #b8c5d2;
    font-size: 11px;
}

.status-ok {
    color: #50d890;
    font-weight: 800;
}

.status-warning {
    color: #ffb347;
    font-weight: 800;
}

.status-error {
    color: #ff6464;
    font-weight: 800;
}

.stButton > button {
    border-radius: 8px !important;
    background: #111a24 !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    border:
        1px solid rgba(255,255,255,.12) !important;
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
    color: #ffffff !important;
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
# Session State
# ============================================================

def init_state():

    defaults = {

        "page": "商品上架工作台",

        "product_name": "",

        "category": DEFAULT_CATEGORY,

        "price": DEFAULT_PRICE,

        "stock": DEFAULT_STOCK,

        "selling_points": "",

        "condition": "全新",

        "images": [],

        "generated": False,

        "published": 0,

        "history": [],

        "gemini_result": "",

        "gemini_model": "",

        "gemini_error": "",

        "api_tested": False,

        "api_status": False,

        "last_generated": {},

    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value


init_state()


# ============================================================
# API Key
# ============================================================

def get_gemini_api_key():

    """
    優先順序：

    1. Streamlit Secrets
    2. 環境變數
    3. 沒有則回傳空字串
    """

    try:

        key = st.secrets.get(
            "GEMINI_API_KEY",
            ""
        )

        if key:

            return str(key).strip()

    except Exception:

        pass

    key = os.environ.get(
        "GEMINI_API_KEY",
        ""
    )

    return key.strip()


# ============================================================
# Gemini SDK
# ============================================================

def get_gemini_client():

    api_key = get_gemini_api_key()

    if not api_key:

        return None, "尚未設定 GEMINI_API_KEY"

    try:

        from google import genai

        client = genai.Client(
            api_key=api_key
        )

        return client, ""

    except ImportError:

        return (
            None,
            "尚未安裝 google-genai，請確認 requirements.txt 有 google-genai"
        )

    except Exception as e:

        return (
            None,
            f"Gemini 初始化失敗：{e}"
        )


# ============================================================
# 清理 Gemini JSON
# ============================================================

def clean_json_text(text):

    if not text:

        return ""

    text = text.strip()

    text = re.sub(
        r"^```json",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```",
        "",
        text
    )

    text = re.sub(
        r"```$",
        "",
        text
    )

    return text.strip()


# ============================================================
# Gemini 圖片分析 Prompt
# ============================================================

def build_gemini_prompt():

    product_name = (
        st.session_state.product_name.strip()
        or "未提供商品名稱"
    )

    category = st.session_state.category

    price = st.session_state.price

    stock = st.session_state.stock

    selling_points = (
        st.session_state.selling_points.strip()
        or "未提供"
    )

    return f"""
你是「AI 蝦皮自動化 2.5 PRO」的商品電商 AI。

你的任務是分析使用者上傳的商品圖片，
並建立可以用於蝦皮、TikTok 與即夢 AI 2.5 的商品內容。

【商品基本資料】

商品名稱：
{product_name}

商品分類：
{category}

商品價格：
NT${price}

商品庫存：
{stock}

使用者提供的商品賣點：
{selling_points}


==================================================
最高優先級：商品圖片真實性
==================================================

你必須把使用者上傳的商品圖片當成商品視覺資訊的唯一來源。

禁止：

1. 不可以虛構品牌。
2. 不可以虛構 Logo。
3. 不可以虛構包裝文字。
4. 不可以虛構商品容量。
5. 不可以虛構成分。
6. 不可以虛構認證。
7. 不可以虛構功效。
8. 不可以虛構圖片中沒有出現的功能。
9. 不可以改變商品外觀。
10. 不可以自行設計新的包裝。
11. 不可以把不存在的文字寫進商品資料。
12. 不可以把圖片看不到的資訊當成確定事實。

如果圖片看不清楚：

請寫：

「圖片無法確認」

不要猜測。


==================================================
商品分析
==================================================

請分析：

1. 商品外觀
2. 包裝形式
3. 可辨識文字
4. 顏色
5. 材質或視覺質感
6. 商品用途
7. 可以安全描述的特色
8. 無法確認的資訊


==================================================
蝦皮標題
==================================================

建立 3 個蝦皮商品標題。

要求：

- 繁體中文
- 自然
- 不要過度誇大
- 不要虛構功效
- 適合蝦皮搜尋
- 優先使用圖片與使用者提供的資訊


==================================================
商品描述
==================================================

建立：

商品介紹

商品特色

使用方式

注意事項

請不要虛構圖片無法確認的資訊。


==================================================
SEO 關鍵字
==================================================

建立 10～20 個適合蝦皮搜尋的關鍵字。


==================================================
TikTok
==================================================

建立一個約 30 秒的 9:16 短影音腳本。

格式：

0-3 秒：
吸睛開場

3-8 秒：
商品出場

8-15 秒：
商品特色

15-23 秒：
使用情境

23-30 秒：
CTA


==================================================
即夢 AI 2.5 Prompt
==================================================

建立一個適合商品短影音生成的 Prompt。

要求：

- 9:16
- 商業廣告風格
- 高質感
- 電商商品攝影
- 緩慢推鏡
- 輕微環繞
- 商品保持原始外觀
- 保持原始包裝
- 保持原始 Logo
- 保持原始文字
- 不改變商品顏色
- 不改變商品比例

禁止：

- 新增 Logo
- 修改 Logo
- 修改包裝
- 修改文字
- 虛構品牌
- 重新設計商品


==================================================
輸出格式
==================================================

請只輸出 JSON。

格式：

{{
    "product_analysis": "",
    "visual_details": "",
    "confirmed_information": "",
    "uncertain_information": "",
    "titles": [
        "",
        "",
        ""
    ],
    "description": "",
    "keywords": [
        "",
        ""
    ],
    "selling_points": [
        "",
        "",
        ""
    ],
    "tiktok_script": "",
    "jimeng_prompt": ""
}}

不要輸出 Markdown。
不要輸出 ```json。
"""


# ============================================================
# Gemini 呼叫
# ============================================================

def call_gemini_with_images(uploaded_files):

    if not uploaded_files:

        return None, "請先上傳至少一張商品圖片。"

    client, error = get_gemini_client()

    if client is None:

        return None, error

    prompt = build_gemini_prompt()

    errors = []

    for model_name in GEMINI_MODELS:

        try:

            contents = []

            contents.append(prompt)

            for uploaded in uploaded_files:

                image_bytes = uploaded.getvalue()

                try:

                    image = Image.open(
                        io.BytesIO(image_bytes)
                    )

                    image = image.convert("RGB")

                    contents.append(image)

                except Exception as image_error:

                    errors.append(
                        f"{uploaded.name}: 圖片讀取失敗：{image_error}"
                    )

            response = client.models.generate_content(
                model=model_name,
                contents=contents
            )

            text = getattr(
                response,
                "text",
                None
            )

            if not text:

                errors.append(
                    f"{model_name}: Gemini 沒有返回文字結果"
                )

                continue

            st.session_state.gemini_model = model_name

            return text, ""

        except Exception as e:

            errors.append(
                f"{model_name}: {str(e)}"
            )

    return (
        None,
        "Gemini 呼叫失敗。\n\n"
        + "\n".join(errors)
    )


# ============================================================
# 解析 Gemini 結果
# ============================================================

def parse_gemini_result(text):

    if not text:

        return {}

    cleaned = clean_json_text(text)

    try:

        return json.loads(cleaned)

    except Exception:

        # 如果 Gemini 回傳不是標準 JSON
        # 保留原始文字，不讓 App 掛掉

        return {
            "product_analysis": cleaned,
            "visual_details": "",
            "confirmed_information": "",
            "uncertain_information": "",
            "titles": [],
            "description": "",
            "keywords": [],
            "selling_points": [],
            "tiktok_script": "",
            "jimeng_prompt": "",
            "raw_text": cleaned
        }


# ============================================================
# 儲存歷史
# ============================================================

def save_history(action):

    record = {
        "時間": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "商品": (
            st.session_state.product_name.strip()
            or DEFAULT_PRODUCT
        ),
        "操作": action,
    }

    st.session_state.history.insert(
        0,
        record
    )


# ============================================================
# 目前商品名稱
# ============================================================

def current_name():

    name = st.session_state.product_name.strip()

    if name:

        return name

    return DEFAULT_PRODUCT


# ============================================================
# 預設內容
# ============================================================

def fallback_title():

    return (
        f"{current_name()}｜"
        f"日常使用｜質感商品"
    )


def fallback_description():

    return f"""
{current_name()}

✨ 商品特色

✓ 商品外觀以實際圖片為準
✓ 適合日常使用
✓ 簡潔商品設計
✓ 購買前請確認商品規格

📌 注意事項

實際商品資訊請以商品包裝、
商品頁面與實際收到的商品為準。
"""


def fallback_keywords():

    return (
        "商品,日常使用,生活用品,"
        "蝦皮,電商,購物"
    )


def fallback_tiktok():

    return f"""
【0-3 秒】
你正在找一款實用的 {current_name()} 嗎？

【3-8 秒】
鏡頭帶出商品完整外觀。

【8-15 秒】
展示商品細節與包裝。

【15-23 秒】
展示日常使用情境。

【23-30 秒】
想了解更多商品資訊，
可以直接查看商品頁面。
"""


def fallback_jimeng():

    return f"""
9:16 vertical premium commercial product video.

Main subject:
{current_name()}

Use the uploaded product image as the ONLY visual source for the product.

Preserve exactly:

- original product shape
- original packaging
- original logo
- original label
- original visible text
- original colors
- original material
- original proportions

Camera:

slow cinematic push-in,
subtle orbit movement,
premium commercial lighting,
clean luxury background,
realistic product photography,
high-end e-commerce advertisement.

Do not redesign the product.

Do not create a new logo.

Do not change packaging.

Do not change visible text.

Do not invent product information.

The product must remain visually consistent
with the uploaded reference image.
"""


# ============================================================
# Sidebar
# ============================================================

def sidebar():

    with st.sidebar:

        st.markdown(
            """
            <div class="card">
                <div style="font-size:20px;font-weight:800">
                    🛍️ AI 蝦皮自動化
                </div>
                <div class="sub">
                    Gemini AI・商品分析・短影音
                </div>
            </div>
            """,
            unsafe_allow_html=True
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
                use_container_width=True
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
                use_container_width=True
            ):

                st.session_state.page = name

                st.rerun()

        api_key = get_gemini_api_key()

        if api_key:

            api_status = (
                '<span class="status-ok">'
                '🟢 Gemini API 已設定'
                '</span>'
            )

        else:

            api_status = (
                '<span class="status-warning">'
                '🟡 尚未設定 Gemini API'
                '</span>'
            )

        st.markdown(
            f"""
            <div class="card">
                <b style="color:#ff8a3d">
                    👑 PRO 會員
                </b>
                <br><br>

                <span class="check">✓</span>
                Gemini 商品分析
                <br>

                <span class="check">✓</span>
                商品圖片分析
                <br>

                <span class="check">✓</span>
                蝦皮文案
                <br>

                <span class="check">✓</span>
                TikTok 9:16
                <br>

                <span class="check">✓</span>
                即夢 AI 2.5 Prompt
                <br>

                <span class="check">✓</span>
                歷史紀錄
                <br><br>

                {api_status}

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# Header
# ============================================================

def header():

    st.markdown(
        """
        <div class="card">
            <div class="title">
                🛍️ AI 蝦皮自動化
                <span class="badge">
                    2.5 PRO
                </span>
            </div>

            <div class="sub">
                Gemini 商品圖片分析・蝦皮內容生成・TikTok・即夢 AI 2.5
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# Metrics
# ============================================================

def metrics():

    cols = st.columns(4)

    values = [
        (
            "今日 AI 使用",
            "0 次",
            "orange"
        ),
        (
            "AI 狀態",
            "Gemini",
            "green"
        ),
        (
            "會員等級",
            "PRO",
            "purple"
        ),
        (
            "會員期限",
            "永久",
            "blue"
        ),
    ]

    for col, data in zip(cols, values):

        label, value, cls = data

        with col:

            st.markdown(
                f"""
                <div class="metric">
                    <div class="metric-label">
                        {label}
                    </div>

                    <div class="metric-value {cls}">
                        {value}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# Dashboard
# ============================================================

def dashboard():

    st.markdown(
        '<div class="section">📊 Dashboard 總覽</div>',
        unsafe_allow_html=True
    )

    cols = st.columns(4)

    data = [
        ("🛍️", "今日上架商品", "0", "+0"),
        ("👁️", "商品瀏覽數", "0", "+0%"),
        ("🛒", "成交訂單", "0", "+0%"),
        ("💰", "銷售額", "NT$0", "+0%"),
    ]

    for col, item in zip(cols, data):

        icon, label, value, delta = item

        with col:

            st.markdown(
                f"""
                <div class="metric">

                    <div style="font-size:23px">
                        {icon}
                    </div>

               
