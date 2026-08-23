import streamlit as st
from PIL import Image
from datetime import datetime
import json
from pathlib import Path


# =========================================================
# AI 蝦皮自動化 3.0 PRO
# Streamlit Cloud 單檔完整版
# =========================================================

APP_NAME = "AI 蝦皮自動化"
APP_VERSION = "3.0 PRO"

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

HISTORY_FILE = DATA_DIR / "history.json"


# =========================================================
# Streamlit 基本設定
# =========================================================

st.set_page_config(
    page_title=f"{APP_NAME} {APP_VERSION}",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CSS
# =========================================================

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
    background: linear-gradient(
        180deg,
        #0a1018,
        #070b11
    );
    border-right: 1px solid rgba(255,255,255,.08);
}

.card {
    background: linear-gradient(
        145deg,
        #101923,
        #090f17
    );
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 14px;
}

.title {
    font-size: 26px;
    font-weight: 800;
}

.sub {
    color: #8995a4;
    font-size: 12px;
}

.section {
    font-size: 18px;
    font-weight: 800;
    margin: 15px 0 10px 0;
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
    background: linear-gradient(
        145deg,
        #111a25,
        #0b1119
    );
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 13px;
    padding: 14px;
    min-height: 85px;
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
    min-width: 130px;
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

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# AI 蝦皮核心指令碼
# =========================================================

AI_SHOPEE_SYSTEM_PROMPT = """
你是「AI 蝦皮自動化」的核心 AI 商品營運智能體。

你的任務是協助電商賣家完成：

1. 商品資料分析
2. 商品圖片分析
3. 商品定位
4. 蝦皮商品標題
5. 蝦皮商品描述
6. 商品賣點
7. SEO 關鍵字
8. TikTok 短影音文案
9. TikTok 9:16 短影音腳本
10. 即夢 AI 商品影片 Prompt
11. 商品上架資料整理

【最高優先規則】

如果有商品圖片：

- 商品圖片是商品視覺資訊的唯一來源。
- 不可以自行修改品牌。
- 不可以自行修改包裝。
- 不可以自行修改產品外型。
- 不可以自行修改產品顏色。
- 不可以自行修改 Logo。
- 不可以自行創造不存在的文字。
- 不可以自行創造不存在的規格。
- 不可以自行創造不存在的功效。
- 不可以自行創造不存在的認證。
- 看不到的內容必須明確說明無法確認。

【商品文案規則】

商品標題：
- 清楚
- 自然
- 適合蝦皮搜尋
- 不使用過度誇張詞語
- 不虛構產品資訊

商品描述：
- 商品名稱
- 商品特色
- 使用情境
- 商品規格
- 注意事項

如果資料不足：
不要猜測。

【TikTok 規則】

影片比例：
9:16

內容流程：

前 3 秒：
吸引注意力

中段：
展示商品

後段：
商品特色

結尾：
行動呼籲

【即夢 AI Prompt 規則】

- 9:16 vertical video
- premium commercial product photography
- cinematic lighting
- slow camera movement
- subtle push-in
- subtle orbit
- realistic product
- preserve original packaging
- preserve original logo
- preserve original label
- preserve original colors
- preserve visible text

禁止：

- redesign product
- fake logo
- fake text
- fake packaging
- changing product shape
- changing product color
- adding unrelated products
- changing brand identity

【輸出內容】

請依照以下結構：

商品分析
商品定位
蝦皮標題
商品描述
商品賣點
SEO 關鍵字
TikTok 文案
TikTok 腳本
即夢 AI Prompt
"""
    

# =========================================================
# Session State
# =========================================================

def init_state():

    defaults = {
        "page": "商品上架工作台",

        "product_name": "",
        "category": "保養保健",
        "price": 499,
        "stock": 100,
        "condition": "全新",
        "selling_points": "",

        "images": [],

        "generated": False,

        "published": 0,

        "history": [],

        "ai_result": "",

        "selected_title": "",

        "api_key": "",
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value


init_state()


# =========================================================
# 歷史紀錄
# =========================================================

def save_history(action):

    record = {
        "時間": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "商品": current_product_name(),
        "操作": action,
    }

    st.session_state.history.insert(0, record)


def current_product_name():

    name = st.session_state.product_name.strip()

    if name:

        return name

    return "尚未輸入商品名稱"


# =========================================================
# 商品分析
# =========================================================

def analyze_product():

    name = current_product_name()

    category = st.session_state.category

    price = st.session_state.price

    stock = st.session_state.stock

    condition = st.session_state.condition

    points = st.session_state.selling_points.strip()

    if not points:

        points = "目前沒有提供額外商品賣點"

    result = f"""
【商品分析】

商品名稱：
{name}

商品分類：
{category}

價格：
NT${price}

庫存：
{stock}

商品狀態：
{condition}

商品賣點：
{points}

【AI 商品定位】

此商品目前可依照：
「{category}」
進行蝦皮商品內容整理。

【注意】

目前這個版本沒有直接連接 Gemini，
因此不會假裝自己已經完成真正的 AI 圖片分析。

如果未來接入 Gemini，
可以將上方的 AI_SHOPEE_SYSTEM_PROMPT
直接作為核心系統指令。

圖片數量：
{len(st.session_state.images)} 張
"""

    return result


# =========================================================
# 標題
# =========================================================

def title_text():

    name = current_product_name()

    if name == "尚未輸入商品名稱":

        name = "商品名稱"

    return (
        f"{name}｜高品質日常使用｜熱門推薦"
    )


def title_variants():

    name = current_product_name()

    if name == "尚未輸入商品名稱":

        name = "商品名稱"

    return [
        f"{name}｜高品質日常使用",
        f"{name}｜熱門推薦｜日常好用",
        f"{name}｜實用商品｜限時優惠",
        f"{name}｜人氣商品｜蝦皮推薦",
    ]


# =========================================================
# 商品描述
# =========================================================

def description_text():

    name = current_product_name()

    points = st.session_state.selling_points.strip()

    if not points:

        points = "商品特色請依實際商品資訊確認"

    return f"""
{name}

✨ 商品特色

✓ {points}

📦 商品資訊

商品分類：
{st.session_state.category}

商品狀態：
{st.session_state.condition}

庫存：
{st.session_state.stock}

💰 商品價格

NT${st.session_state.price}

⚠️ 注意事項

實際商品資訊請以商品實物、
商品包裝與賣場資訊為準。

如有任何規格疑問，
請購買前先確認商品資訊。
"""


# =========================================================
# SEO
# =========================================================

def keywords_text():

    name = current_product_name()

    category = st.session_state.category

    return (
        f"{name},"
        f"{category},"
        "蝦皮,"
        "網路購物,"
        "熱門商品,"
        "日常用品,"
        "推薦商品"
    )


# =========================================================
# TikTok
# =========================================================

def tiktok_text():

    name = current_product_name()

    return f"""
🔥 {name}

還在找適合自己的商品嗎？

這次直接帶你快速看看：

✨ 商品特色展示
✨ 商品外觀展示
✨ 實際使用情境
✨ 商品細節

如果你正在找：

「{name}」

可以進一步查看商品資訊。

🛒 想了解更多，
直接查看賣場！
"""


# =========================================================
# TikTok 腳本
# =========================================================

def tiktok_script():

    name = current_product_name()

    return f"""
【0-3 秒｜Hook】

畫面：
快速展示 {name}

字幕：
「最近很多人都在找這個！」

旁白：
「如果你正在找 {name}，先看這裡。」

--------------------------------

【3-8 秒｜商品展示】

畫面：
商品近距離展示。

鏡頭慢慢推近。

字幕：
「商品細節一次看」

--------------------------------

【8-15 秒｜特色】

畫面：
依照商品實際特色展示。

字幕：
「實際商品資訊請以商品為準」

--------------------------------

【15-20 秒｜結尾】

畫面：
商品正面展示。

字幕：
「想了解更多，查看賣場」

旁白：
「想知道更多商品資訊，
直接到賣場看看。」
"""


# =========================================================
# 即夢 Prompt
# =========================================================

def jimeng_prompt():

    name = current_product_name()

    return f"""
9:16 vertical premium commercial product video.

MAIN SUBJECT:
{name}

SOURCE RULE:
Use the uploaded product image as the ONLY visual source
for the actual product.

PRODUCT CONSISTENCY:

Preserve the original:

- product shape
- packaging
- brand
- logo
- label
- visible text
- colors
- materials
- proportions
- physical appearance

CAMERA:

Slow cinematic push-in.

Subtle orbit movement.

Smooth professional camera motion.

PREMIUM STYLE:

Luxury commercial photography.

Clean studio environment.

Soft cinematic lighting.

Realistic shadows.

Natural reflections.

High detail.

Photorealistic product presentation.

BACKGROUND:

Clean premium background.

The background must not change
the actual product identity.

IMPORTANT:

Do not redesign the product.

Do not create a new package.

Do not invent a logo.

Do not invent text.

Do not change the brand.

Do not change the product color.

Do not change the product shape.

Do not add fake product information.

Do not create unrelated products.

The uploaded image remains
the authoritative source for the product.
"""


# =========================================================
# Sidebar
# =========================================================

def sidebar():

    with st.sidebar:

        st.markdown(
            """
            <div class="card">
                <div style="font-size:20px;font-weight:800">
                    🛍️ AI 蝦皮自動化
                </div>
                <div class="sub">
                    AI 商品營運智能中心
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
                    👑 PRO
                </b>
                <br><br>

                <span class="check">✓</span>
                商品分析
                <br>

                <span class="check">✓</span>
                商品圖片
                <br>

                <span class="check">✓</span>
                蝦皮文案
                <br>

                <span class="check">✓</span>
                TikTok 9:16
                <br>

                <span class="check">✓</span>
                即夢 Prompt
                <br>

                <span class="check">✓</span>
                歷史紀錄
                <br>

                <span class="check">✓</span>
                AI 指令碼
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# Header
# =========================================================

def header():

    st.markdown(
        f"""
        <div class="card">

            <div class="title">
                🛍️ {APP_NAME}

                <span class="badge">
                    {APP_VERSION}
                </span>
            </div>

            <div class="sub">
                AI 商品分析・蝦皮文案・TikTok・即夢 Prompt
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# Metrics
# =========================================================

def metrics():

    cols = st.columns(4)

    values = [
        (
            "AI 工作流",
            "READY",
            "orange",
        ),
        (
            "圖片",
            f"{len(st.session_state.images)} 張",
            "green",
        ),
        (
            "模擬上架",
            f"{st.session_state.published} 次",
            "purple",
        ),
        (
            "系統",
            "正常",
            "blue",
        ),
    ]

    for col, (label, value, cls) in zip(
        cols,
        values,
    ):

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
                unsafe_allow_html=True,
            )


# =========================================================
# Dashboard
# =========================================================

def dashboard():

    st.markdown(
        '<div class="section">📊 Dashboard</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(4)

    data = [
        ("🛍️", "今日上架", "12", "+3"),
        ("👁️", "瀏覽數", "5,689", "+22%"),
        ("🛒", "成交訂單", "58", "+15%"),
        ("💰", "銷售額", "NT$28,560", "+25%"),
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

                    <div class="metric-label">
                        {label}
                    </div>

                    <div class="metric-value">
                        {value}
                    </div>

                    <div class="green">
                        {delta}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div class="section">🚀 AI 工作流程</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="workflow">

            <div class="step">
                <div class="step-icon">📝</div>
                <div class="step-title">
                    商品輸入
                </div>
                <div class="step-desc">
                    商品資料與圖片
                </div>
            </div>

            <div class="arrow">→</div>

            <div class="step">
                <div class="step-icon">🧠</div>
                <div class="step-title">
                    AI 分析
                </div>
                <div class="step-desc">
                    商品分析
                </div>
            </div>

            <div class="arrow">→</div>

            <div class="step">
                <div class="step-icon">✨</div>
                <div class="step-title">
                    內容生成
                </div>
                <div class="step-desc">
                    文案與 Prompt
                </div>
            </div>

            <div class="arrow">→</div>

            <div class="step">
                <div class="step-icon">🛒</div>
                <div class="step-title">
                    蝦皮
                </div>
                <div class="step-desc">
                    上架資料
                </div>
            </div>

            <div class="arrow">→</div>

            <div class="step">
                <div class="step-icon">🎵</div>
                <div class="step-title">
                    TikTok
                </div>
                <div class="step-desc">
                    9:16 短影音
                </div>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.line_chart(
        {
            "銷售額": [
                18000,
                21000,
                19500,
                26000,
                24500,
                28000,
                28560,
            ]
        }
    )


# =========================================================
# Workflow Header
# =========================================================

def workflow_header():

    st.markdown(
        """
        <div class="workflow">

            <div class="step">
                <div class="step-icon">📝</div>
                <div class="step-title">
                    商品資訊
                </div>
                <div class="step-desc">
                    商品資料
                </div>
            </div>

            <div class="arrow">→</div>

            <div class="step">
                <div class="step-icon">🧠</div>
                <div class="step-title">
                    AI 分析
                </div>
                <div class="step-desc">
                    商品與圖片
                </div>
            </div>

            <div class="arrow">→</div>

            <div class="step">
                <div class="step-icon">✨</div>
                <div class="step-title">
                    AI 生成
                </div>
                <div class="step-desc">
                    文案與 Prompt
                </div>
            </div>

            <div class="arrow">→</div>

            <div class="step">
                <div class="step-icon">🚀</div>
                <div class="step-title">
                    上架
                </div>
                <div class="step-desc">
                    模擬上架
                </div>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 商品工作台
# =========================================================

def workspace():

    workflow_header()

    left, middle, right = st.columns(
        [1.05, 1.2, 1.25]
    )

    # -----------------------------------------------------
    # 左邊
    # -----------------------------------------------------

    with left:

        st.markdown(
            '<div class="card"
