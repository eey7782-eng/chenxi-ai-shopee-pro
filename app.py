# ============================================================
# AI 蝦皮自動化 2.5 PRO
# 單檔 Streamlit Cloud 版本
#
# 功能：
# 1. 商品資料輸入
# 2. 商品圖片上傳與預覽
# 3. AI 商品分析
# 4. 蝦皮標題生成
# 5. 商品描述生成
# 6. 關鍵字生成
# 7. TikTok 9:16 文案
# 8. 即夢 AI 2.5 Prompt
# 9. AI 蝦皮核心指令碼
# 10. 商品管理
# 11. 歷史紀錄
# 12. AI 素材庫
# 13. API 設定
# 14. Dashboard
#
# 注意：
# - 未設定 Gemini API Key 時，可以使用內建離線 AI 模擬模式
# - 本版本不會假裝真的發布到蝦皮
# - 「一鍵上架」目前為模擬上架
# ============================================================

import io
import json
from datetime import datetime

import streamlit as st
from PIL import Image


# ============================================================
# 基本設定
# ============================================================

APP_NAME = "AI 蝦皮自動化"
APP_VERSION = "2.5 PRO"

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
            rgba(255, 90, 0, 0.08),
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
    padding: 16px;
    margin-bottom: 14px;
}

.title {
    font-size: 24px;
    font-weight: 800;
}

.sub {
    color: #8995a4;
    font-size: 12px;
}

.section {
    font-size: 17px;
    font-weight: 800;
    margin: 10px 0;
}

.badge {
    display: inline-block;
    margin-left: 8px;
    padding: 3px 8px;
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
        "ai_mode": "離線 AI 模式",
        "gemini_api_key": "",
        "generated_data": {},
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


# ============================================================
# AI 蝦皮核心指令碼
# ============================================================

AI_SHOPEE_CORE_RULES = """
你是「AI 蝦皮自動化 2.5 PRO」核心智能體。

你的主要任務：

【第一階段：商品資料理解】
1. 讀取商品名稱。
2. 讀取商品分類。
3. 讀取商品價格。
4. 讀取商品庫存。
5. 讀取商品賣點。
6. 讀取使用者上傳的商品圖片。

【第二階段：商品分析】
1. 判斷商品類型。
2. 整理商品特色。
3. 整理使用者提供的賣點。
4. 不可以把不存在的商品資訊當成事實。
5. 不可以憑空增加品牌。
6. 不可以憑空增加規格。
7. 不可以憑空增加容量。
8. 不可以憑空增加成分。
9. 不可以憑空增加認證。
10. 不可以憑空增加功效。

【第三階段：蝦皮標題】
產生適合蝦皮搜尋的商品標題。
標題要：
- 清楚
- 容易搜尋
- 不亂誇大
- 不虛構品牌
- 不虛構規格
- 不使用不合理的保證性詞語

【第四階段：商品描述】
建立：
- 商品特色
- 使用情境
- 商品資訊
- 購買提醒

描述必須以使用者提供資料為基礎。

【第五階段：關鍵字】
產生適合商品搜尋的關鍵字。
關鍵字必須和商品有關。

【第六階段：TikTok】
產生 9:16 短影音文案。
內容包含：
- 前 3 秒 Hook
- 商品介紹
- 商品特色
- 使用情境
- CTA

【第七階段：即夢 AI 2.5】
商品影片必須：
- 9:16
- 商品作為主要視覺
- 保留原商品外觀
- 保留包裝
- 保留 Logo
- 保留標籤
- 保留原本顏色
- 保留材質
- 保留可見文字

禁止：
- 改品牌
- 改 Logo
- 改包裝
- 改產品形狀
- 憑空產生文字
- 憑空增加商品
- 把商品重新設計

建議鏡頭：
- slow cinematic push-in
- subtle orbit
- premium commercial lighting
- clean background
- product hero shot

【最重要規則】
如果圖片中看不到某項資料，不可以假裝看到了。
如果使用者沒有提供資料，不可以自行宣稱該資料是真實商品資訊。
"""


# ============================================================
# Helper
# ============================================================

def current_name():
    name = str(st.session_state.product_name).strip()

    if name:
        return name

    return "玻尿酸保濕精華液"


def current_category():
    return st.session_state.category


def current_price():
    return int(st.session_state.price)


def current_stock():
    return int(st.session_state.stock)


def get_product_data():
    return {
        "product_name": current_name(),
        "category": current_category(),
        "price": current_price(),
        "stock": current_stock(),
        "selling_points": st.session_state.selling_points,
        "condition": st.session_state.condition,
    }


# ============================================================
# 商品分類
# ============================================================

def detect_product_category(text):
    text = str(text).lower()

    categories = {
        "美妝保養": [
            "洗面",
            "精華",
            "乳液",
            "面膜",
            "化妝水",
            "防曬",
            "保濕",
            "美容",
            "保養",
            "洗髮",
        ],
        "3C 電子": [
            "手機",
            "平板",
            "耳機",
            "充電",
            "鍵盤",
            "滑鼠",
            "電腦",
            "螢幕",
        ],
        "居家生活": [
            "收納",
            "清潔",
            "杯",
            "餐具",
            "家用",
            "居家",
        ],
        "服飾鞋包": [
            "衣",
            "褲",
            "鞋",
            "包",
            "帽",
            "襪",
        ],
        "食品飲料": [
            "零食",
            "餅乾",
            "飲料",
            "茶",
            "咖啡",
            "食品",
        ],
        "汽機車": [
            "汽車",
            "機車",
            "車用",
            "汽機車",
        ],
    }

    for category, words in categories.items():
        for word in words:
            if word.lower() in text:
                return category

    return "其他"


# ============================================================
# AI 生成內容
# ============================================================

def generate_title(product):
    name = product["product_name"]
    points = product["selling_points"].strip()

    if points:
        first_point = points.split("、")[0]
        return f"{name}｜{first_point}｜日常使用推薦"

    return f"{name}｜實用推薦｜日常生活好物"


def generate_description(product):
    name = product["product_name"]
    category = product["category"]
    price = product["price"]
    condition = product["condition"]
    points = product["selling_points"].strip()

    if points:
        point_list = [
            x.strip()
            for x in points.replace(",", "、").split("、")
            if x.strip()
        ]
    else:
        point_list = [
            "商品特色依實際商品為準",
            "適合日常使用",
            "簡單方便",
        ]

    point_text = "\n".join(
        f"✓ {item}"
        for item in point_list[:8]
    )

    return f"""
【商品名稱】
{name}

【商品分類】
{category}

【商品狀態】
{condition}

【商品特色】
{point_text}

【商品價格】
NT${price}

【購買提醒】
・商品資訊請以實際商品包裝及賣場資訊為準。
・不同螢幕可能造成顏色顯示差異。
・下單前請確認商品規格及數量。
・如有任何問題，歡迎先詢問賣家。

【AI 內容生成】
以上內容依照目前輸入的商品資料建立，
沒有加入未提供的品牌、規格或認證資訊。
""".strip()


def generate_keywords(product):
    name = product["product_name"]

    base = [
        name,
        product["category"],
        "日常好物",
        "生活用品",
        "熱門商品",
        "網路推薦",
        "蝦皮購物",
    ]

    if product["selling_points"]:
        extra = [
            x.strip()
            for x in product["selling_points"]
            .replace(",", "、")
            .split("、")
            if x.strip()
        ]

        base.extend(extra)

    unique = []

    for item in base:
        if item and item not in unique:
            unique.append(item)

    return ",".join(unique[:15])


def generate_tiktok(product):
    name = product["product_name"]

    points = product["selling_points"].strip()

    if points:
        point_text = points
    else:
        point_text = "實用、方便、適合日常使用"

    return f"""
【TikTok 9:16 短影音腳本】

0-3 秒｜HOOK
「最近正在找 {name} 嗎？」

3-8 秒｜商品出場
畫面快速展示商品正面與包裝。
字幕：
「{name}」

8-15 秒｜商品特色
展示商品細節。
字幕：
「{point_text}」

15-22 秒｜使用情境
用自然生活場景呈現商品使用方式。

22-27 秒｜商品特寫
慢速推近商品。
展示包裝、外觀與細節。

27-30 秒｜CTA
「想了解更多商品資訊，直接查看賣場！」

格式：
9:16 Vertical
適合 TikTok / Reels / Shorts
""".strip()


def generate_jimeng_prompt(product):
    name = product["product_name"]

    return f"""
【即夢 AI 2.5 商品影片 Prompt】

9:16 vertical premium commercial product video.

Main subject:
{name}

IMPORTANT PRODUCT CONSISTENCY RULE:

Use the uploaded product image as the ONLY visual source for the product.

Preserve:
- original product shape
- original packaging
- original logo
- original label
- original visible text
- original colors
- original materials
- original proportions

Camera:
slow cinematic push-in,
subtle orbit movement,
premium commercial product photography,
soft studio lighting,
clean luxury background,
high-end e-commerce advertisement,
realistic product presentation.

Scene:
The product remains the main subject.
Camera slowly moves around the product.
Use subtle reflections and realistic shadows.
Keep the product centered and clearly visible.

DO NOT:
redesign the product,
change packaging,
change logo,
change product shape,
change product color,
invent text,
invent logo,
invent ingredients,
invent certification,
add fake brand information,
replace the original product.

The product must remain visually consistent
with the uploaded source image.

Output:
9:16 vertical commercial product video.
""".strip()


def generate_analysis(product):
    name = product["product_name"]

    category = product["category"]

    price = product["price"]

    stock = product["stock"]

    points = product["selling_points"].strip()

    if not points:
        points = "目前尚未提供商品賣點"

    return f"""
【AI 商品分析】

商品：
{name}

分類：
{category}

價格：
NT${price}

庫存：
{stock}

使用者提供賣點：
{points}

AI 判斷：

1. 商品名稱已建立。
2. 商品分類已建立。
3. 價格資料已建立。
4. 庫存資料已建立。
5. 可進一步建立蝦皮標題。
6. 可建立商品描述。
7. 可建立搜尋關鍵字。
8. 可建立 TikTok 9:16 文案。
9. 可建立即夢 AI 2.5 商品影片 Prompt。

圖片分析規則：

本系統不會在沒有實際 AI 圖像辨識 API
的情況下假裝辨識圖片內容。

如果啟用 Gemini，
才會進一步使用 Gemini 進行圖片分析。
""".strip()


# ============================================================
# 工作流
# ============================================================

def run_ai_workflow():
    product = get_product_data()

    result = {
        "analysis": generate_analysis(product),
        "title": generate_title(product),
        "description": generate_description(product),
        "keywords": generate_keywords(product),
        "tiktok": generate_tiktok(product),
        "jimeng": generate_jimeng_prompt(product),
        "rules": AI_SHOPEE_CORE_RULES,
    }

    st.session_state.generated_data = result
    st.session_state.generated = True

    save_history("執行 AI 蝦皮工作流")


# ============================================================
# History
# ============================================================

def save_history(action):
    record = {
        "時間": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "商品": current_name(),
        "操作": action,
    }

    st.session_state.history.insert(0, record)

    if len(st.session_state.history) > 100:
        st.session_state.history = (
            st.session_state.history[:100]
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
AI 智能生成・商品工作流
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

<span class="check">✓</span>
AI 商品內容生成

<br>

<span class="check">✓</span>
商品圖片介面

<br>

<span class="check">✓</span>
TikTok 9:16

<br>

<span class="check">✓</span>
即夢 AI 2.5 Prompt

<br>

<span class="check">✓</span>
歷史紀錄

<br>

<span class="check">✓</span>
AI 蝦皮核心指令碼

</div>
""",
            unsafe_allow_html=True,
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
AI 智能生成・商品工作流・蝦皮上架準備
</div>

</div>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# Metrics
# ============================================================

def metrics():

    columns = st.columns(4)

    values = [
        (
            "今日 AI 使用額度",
            "86 / 200 次",
            "orange",
        ),
        (
            "AI 模
