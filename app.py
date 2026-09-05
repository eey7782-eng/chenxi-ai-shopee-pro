# ============================================================
# 黑金剛 AI 多 AI 總控中心 PRO
# VERSION 3.0 NO-API
# ============================================================
#
# 核心：
# 商品資料
#    ↓
# 黑金剛 AI 指令碼引擎
#    ↓
# ┌──────────────┬──────────────┬──────────────┐
# │ 多 AI        │ 電商          │ 短影音       │
# │ ChatGPT      │ Shopee        │ TikTok       │
# │ Gemini       │ 商品文案       │ 即夢 AI      │
# │ DeepSeek     │ 商品分析       │ AI影片腳本   │
# │ Claude       │ 關鍵字         │ AI圖片Prompt │
# │ Grok         │                │              │
# └──────────────┴──────────────┴──────────────┘
#
# NO-API：
# 本系統不直接呼叫外部 AI API。
# 系統負責建立高品質 AI 指令，使用者再開啟對應 AI 平台執行。
#
# ============================================================

import io
import os
import re
import json
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, date, timedelta

import streamlit as st
from PIL import Image, ImageOps


# ============================================================
# 基本設定
# ============================================================

APP_NAME = "黑金剛 AI 多 AI 總控中心 PRO"
APP_VERSION = "3.0 NO-API"

DATA_DIR = Path("data")
MEDIA_DIR = DATA_DIR / "media"
HISTORY_DIR = DATA_DIR / "history"

MEMBERS_FILE = DATA_DIR / "members.json"
PRODUCTS_FILE = DATA_DIR / "products.json"
HISTORY_FILE = DATA_DIR / "history.json"

MAX_IMAGE_MB = 20
MAX_IMAGE_SIZE = 1600

DEFAULT_MEMBER_DAYS = 30

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

DATA_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Streamlit 頁面
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🖤",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

html, body, [class*="css"] {
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top right, rgba(180,140,40,0.10), transparent 30%),
        radial-gradient(circle at top left, rgba(80,80,80,0.08), transparent 25%),
        #080808;
}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}

.bk-hero {
    padding: 28px;
    border-radius: 22px;
    margin-bottom: 22px;
    background:
        linear-gradient(135deg, #181818 0%, #0c0c0c 60%, #16120a 100%);
    border: 1px solid #3d3320;
    box-shadow: 0 10px 40px rgba(0,0,0,0.35);
}

.bk-hero h1 {
    margin: 0;
    font-size: 34px;
    font-weight: 900;
    letter-spacing: 1px;
}

.bk-hero p {
    margin-top: 10px;
    color: #aaa;
    font-size: 15px;
}

.bk-card {
    background: #111111;
    border: 1px solid #292929;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 16px;
}

.bk-card:hover {
    border-color: #57482b;
}

.bk-title {
    font-size: 21px;
    font-weight: 800;
    margin-bottom: 8px;
}

.bk-small {
    color: #999;
    font-size: 13px;
}

.bk-big {
    font-size: 30px;
    font-weight: 900;
}

.bk-tag {
    display: inline-block;
    background: #211c12;
    color: #d9b86c;
    border: 1px solid #594824;
    border-radius: 999px;
    padding: 4px 10px;
    margin: 3px;
    font-size: 12px;
}

.bk-success {
    background: #102014;
    border: 1px solid #274a2c;
    color: #9bdd9e;
    padding: 12px;
    border-radius: 12px;
}

.bk-warning {
    background: #251d0d;
    border: 1px solid #59471e;
    color: #e5c36d;
    padding: 12px;
    border-radius: 12px;
}

.bk-danger {
    background: #250f0f;
    border: 1px solid #542323;
    color: #e79a9a;
    padding: 12px;
    border-radius: 12px;
}

div[data-testid="stMetric"] {
    background: #111111;
    border: 1px solid #292929;
    padding: 16px;
    border-radius: 16px;
}

section[data-testid="stSidebar"] {
    background: #090909;
    border-right: 1px solid #252525;
}

section[data-testid="stSidebar"] .stButton button {
    text-align: left;
}

.stButton > button {
    border-radius: 10px;
    font-weight: 700;
}

.stDownloadButton > button {
    border-radius: 10px;
}

textarea {
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif !important;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# JSON 工具
# ============================================================

def load_json(path, default):
    try:
        if not path.exists():
            return default

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        return default


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2,
            )
        return True

    except Exception:
        return False


# ============================================================
# 密碼
# ============================================================

def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# ============================================================
# 檔名
# ============================================================

def safe_filename(text):
    text = str(text or "file")

    text = re.sub(
        r"[^A-Za-z0-9\u4e00-\u9fff_-]+",
        "_",
        text,
    )

    text = text.strip("_")

    if not text:
        text = "file"

    return text[:80]


# ============================================================
# 初始化資料
# ============================================================

def init_data():

    members = load_json(MEMBERS_FILE, {})

    if not isinstance(members, dict):
        members = {}

    if ADMIN_USERNAME not in members:

        members[ADMIN_USERNAME] = {
            "password": hash_password(ADMIN_PASSWORD),
            "role": "admin",
            "expires": "2099-12-31",
            "created": datetime.now().isoformat(),
        }

        save_json(MEMBERS_FILE, members)

    if not PRODUCTS_FILE.exists():
        save_json(PRODUCTS_FILE, [])

    if not HISTORY_FILE.exists():
        save_json(HISTORY_FILE, [])


init_data()


# ============================================================
# Session
# ============================================================

def init_session():

    st.session_state.setdefault(
        "logged_in",
        False,
    )

    st.session_state.setdefault(
        "user",
        "",
    )

    st.session_state.setdefault(
        "role",
        "member",
    )

    st.session_state.setdefault(
        "last_product",
        {},
    )

    st.session_state.setdefault(
        "generated_prompt",
        "",
    )


init_session()


# ============================================================
# 會員
# ============================================================

def is_expired(member):

    try:
        if member.get("role") == "admin":
            return False

        expires = datetime.fromisoformat(
            member["expires"]
        ).date()

        return date.today() > expires

    except Exception:
        return True


def login_user(username, password):

    members = load_json(
        MEMBERS_FILE,
        {},
    )

    member = members.get(username)

    if not member:
        return False, "帳號不存在"

    if member.get("password") != hash_password(password):
        return False, "密碼錯誤"

    if is_expired(member):
        return False, "會員期限已到期"

    st.session_state.logged_in = True
    st.session_state.user = username
    st.session_state.role = member.get(
        "role",
        "member",
    )

    return True, "登入成功"


def register_user(username, password):

    username = username.strip()

    if len(username) < 3:
        return False, "帳號至少 3 個字元"

    if len(password) < 6:
        return False, "密碼至少 6 個字元"

    members = load_json(
        MEMBERS_FILE,
        {},
    )

    if username in members:
        return False, "帳號已存在"

    expires = (
        date.today()
        + timedelta(days=DEFAULT_MEMBER_DAYS)
    ).isoformat()

    members[username] = {
        "password": hash_password(password),
        "role": "member",
        "expires": expires,
        "created": datetime.now().isoformat(),
    }

    if save_json(MEMBERS_FILE, members):
        return True, "註冊成功，請登入"

    return False, "資料儲存失敗"


# ============================================================
# 歷史
# ============================================================

def add_history(kind, title, content):

    history = load_json(
        HISTORY_FILE,
        [],
    )

    if not isinstance(history, list):
        history = []

    history.insert(
        0,
        {
            "id": secrets.token_hex(8),
            "time": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "user": st.session_state.get(
                "user",
                "",
            ),
            "kind": kind,
            "title": title,
            "content": content,
        },
    )

    history = history[:500]

    save_json(
        HISTORY_FILE,
        history,
    )


# ============================================================
# 商品
# ============================================================

def save_product(data):

    products = load_json(
        PRODUCTS_FILE,
        [],
    )

    if not isinstance(products, list):
        products = []

    item = dict(data)

    item["id"] = secrets.token_hex(8)

    item["created"] = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    item["user"] = st.session_state.get(
        "user",
        "",
    )

    products.insert(
        0,
        item,
    )

    save_json(
        PRODUCTS_FILE,
        products,
    )

    st.session_state.last_product = item

    return item


def delete_product(product_id):

    products = load_json(
        PRODUCTS_FILE,
        [],
    )

    new_products = [
        p for p in products
        if p.get("id") != product_id
    ]

    save_json(
        PRODUCTS_FILE,
        new_products,
    )


# ============================================================
# 商品分類
# ============================================================

def detect_product_category(text):

    text = str(text or "").lower()

    categories = {

        "食品": [
            "芭樂",
            "水果",
            "零食",
            "餅乾",
            "茶",
            "咖啡",
            "食品",
            "肉乾",
            "堅果",
            "糖",
        ],

        "保養美妝": [
            "洗面",
            "乳液",
            "精華",
            "面膜",
            "防曬",
            "洗髮",
            "保養",
            "香水",
            "化妝",
        ],

        "3C": [
            "手機",
            "平板",
            "耳機",
            "充電",
            "鍵盤",
            "滑鼠",
            "電腦",
            "3c",
            "充電器",
        ],

        "居家生活": [
            "清潔",
            "收納",
            "杯",
            "鍋",
            "家居",
            "居家",
            "用品",
        ],

        "服飾": [
            "衣",
            "褲",
            "鞋",
            "襪",
            "包",
            "帽",
            "服飾",
        ],

        "汽機車": [
            "汽車",
            "機車",
            "車用",
            "行車記錄器",
            "輪胎",
        ],
    }

    for category, words in categories.items():

        for word in words:

            if word.lower() in text:
                return category

    return "其他"


# ============================================================
# 圖片儲存
# ============================================================

def save_uploaded_image(uploaded_file, product_name):

    if uploaded_file is None:
        return ""

    try:

        raw = uploaded_file.getvalue()

        if len(raw) > MAX_IMAGE_MB * 1024 * 1024:
            return ""

        image = Image.open(
            io.BytesIO(raw)
        )

        image = ImageOps.exif_transpose(
            image
        )

        if image.width > MAX_IMAGE_SIZE or image.height > MAX_IMAGE_SIZE:

            image.thumbnail(
                (
                    MAX_IMAGE_SIZE,
                    MAX_IMAGE_SIZE,
                )
            )

        if image.mode not in (
            "RGB",
            "RGBA",
        ):
            image = image.convert("RGB")

        filename = (
            safe_filename(product_name)
            + "_"
            + datetime.now().strftime(
                "%Y%m%d%H%M%S"
            )
            + ".jpg"
        )

        path = MEDIA_DIR / filename

        image.save(
            path,
            "JPEG",
            quality=92,
        )

        return str(path)

    except Exception:
        return ""


# ============================================================
# 商品表單
# ============================================================

def product_form(prefix="main"):

    st.markdown(
        '<div class="bk-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="bk-title">📦 商品資料</div>',
        unsafe_allow_html=True,
    )

    name = st.text_input(
        "商品名稱",
        placeholder="例如：甘草芭樂、UNO洗面乳、藍牙耳機",
        key=f"{prefix}_name",
    )

    auto_category = detect_product_category(
        name
    )

    categories = [
        "食品",
        "保養美妝",
        "3C",
        "居家生活",
        "服飾",
        "汽機車",
        "其他",
    ]

    default_index = (
        categories.index(auto_category)
        if auto_category in categories
        else 6
    )

    category = st.selectbox(
        "商品分類",
        categories,
        index=default_index,
        key=f"{prefix}_category",
    )

    col1, col2 = st.columns(2)

    with col1:

        price = st.number_input(
            "商品售價",
            min_value=0,
            value=999,
            step=1,
            key=f"{prefix}_price",
        )

    with col2:

        seconds = st.selectbox(
            "TikTok 影片秒數",
            [15, 30, 60],
            index=0,
            key=f"{prefix}_seconds",
        )

    points = st.text_area(
        "商品賣點",
        placeholder=(
            "請輸入你已確認的商品資訊。\n"
            "例如：容量、材質、功能、口味、尺寸、特色等。\n"
            "沒有資料的部分，AI 不得自行編造。"
        ),
        height=140,
        key=f"{prefix}_points",
    )

    uploaded = st.file_uploader(
        "商品原圖",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
        ],
        key=f"{prefix}_image",
    )

    image_path = ""

    if uploaded:

        try:

            raw = uploaded.getvalue()

            image = Image.open(
                io.BytesIO(raw)
            )

            image = ImageOps.exif_transpose(
                image
            )

            st.image(
                image,
                width=280,
            )

            image_path = save_uploaded_image(
                uploaded,
                name or "product",
            )

        except Exception:
            st.error("圖片無法讀取")

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    return {
        "name": name.strip(),
        "category": category,
        "price": price,
        "points": points.strip(),
        "image_path": image_path,
        "seconds": seconds,
    }


# ============================================================
# 商品資料格式
# ============================================================

def product_context(data):

    return f"""
【商品名稱】
{data.get("name", "")}

【商品分類】
{data.get("category", "")}

【售價】
NT$ {data.get("price", 0)}

【已確認商品賣點】
{data.get("points", "")}

【圖片】
已提供商品原圖時，只能以原圖作為視覺依據。

【重要規則】
1. 不得自行發明品牌。
2. 不得自行發明型號。
3. 不得自行發明容量。
4. 不得自行發明尺寸。
5. 不得自行發明材質。
6. 不得自行發明功效。
7. 不得自行發明認證。
8. 不得自行發明包裝文字。
9. 不得修改 Logo。
10. 不得修改商品顏色、形狀、包裝與結構。
11. 無法確認的資料請明確標示「無法確認，請人工確認」。
"""


# ============================================================
# Shopee
# ============================================================

def generate_shopee_copy(data):

    name = data.get("name", "")
    category = data.get("category", "")
    price = data.get("price", 0)
    points = data.get("points", "")

    return f"""
【蝦皮商品標題 1】
{name}｜{category}｜熱門商品｜限時優惠

【蝦皮商品標題 2】
{name}｜{category}｜精選推薦｜快速出貨

【蝦皮商品標題 3】
{name}｜{category}｜人氣推薦｜超值選擇

【商品描述】
商品名稱：{name}
商品分類：{category}
售價：NT$ {price}

商品賣點：
{points}

【購買提醒】
實際商品規格、尺寸、顏色、包裝與內容物，
請以商品實際照片及賣家提供資訊為準。

【關鍵字】
{name}
{category}
網路熱賣
人氣推薦
優惠商品
"""

    
# ============================================================
# TikTok
# ============================================================

def generate_tiktok(data, seconds=15):

    name = data.get("name", "")
    points = data.get("points", "")

    point_lines = [
        x.strip()
        for x in re.split(
            r"[\n,，。；;]+",
            points,
        )
        if x.strip()
    ]

    p1 = (
        point_lines[0]
        if len(point_lines) > 0
        else "第一個已確認商品賣點"
    )

    p2 = (
        point_lines[1]
        if len(point_lines) > 1
        else "第二個已確認商品賣點"
    )

    if seconds == 15:

        return f"""
【TikTok 15 秒短影音腳本】

0-3 秒｜Hook
「如果你正在找{name}，先看這裡！」

3-7 秒｜賣點
畫面展示商品原圖。
字幕：
{p1}

7-11 秒｜第二賣點
近距離展示商品。
字幕：
{p2}

11-15 秒｜CTA
「想了解更多，點擊商品連結看看！」

【拍攝規則】
商品外觀必須維持原樣。
不得修改品牌、Logo、包裝、文字、顏色、形狀。

【影片比例】
9:16
"""

    if seconds == 30:

        return f"""
【TikTok 30 秒短影音腳本】

0-3 秒｜Hook
「這個{name}到底有什麼特色？」

3-8 秒｜商品展示
展示商品整體外觀。

8-14 秒｜賣點一
{p1}

14-20 秒｜賣點二
{p2}

20-25 秒｜使用情境
只呈現已知且合理的使用情境，
不得虛構商品功能。

25-30 秒｜CTA
「喜歡的話，可以點進商品頁了解！」

【影片比例】
9:16
"""

    return f"""
【TikTok 60 秒短影音腳本】

0-5 秒｜強力 Hook
「如果你最近正在找{name}，這個可以先看看。」

5-15 秒｜商品展示
展示商品正面、側面、細節。

15-25 秒｜賣點一
{p1}

25-35 秒｜賣點二
{p2}

35-45 秒｜商品細節
展示包裝、材質、外觀與細節。
只能呈現原圖能確認的內容。

45-53 秒｜購買理由
整理已確認的商品優勢。

53-60 秒｜CTA
「想了解完整資訊，直接點進商品頁！」

【影片比例】
9:16
"""


# ============================================================
# 即夢圖片 Prompt
# ============================================================

def generate_jimeng_image(data, ratio="9:16"):

    name = data.get("name", "")
    category = data.get("category", "")
    points = data.get("points", "")

    return f"""
【即夢 AI 商品圖片生成指令】

請以「上傳的商品原圖」作為唯一商品視覺來源。

商品名稱：
{name}

商品分類：
{category}

已確認賣點：
{points}

【核心要求】

1. 必須保留原商品。
2. 不得重新設計商品。
3. 不得改變商品外型。
4. 不得改變商品顏色。
5. 不得改變商品材質。
6. 不得改變包裝。
7. 不得修改 Logo。
8. 不得修改品牌名稱。
9. 不得修改包裝上的文字。
10. 不得新增不存在的規格。
11. 不得新增不存在的功能。
12. 不得讓商品變形。
13. 不得生成不存在的配件。

【畫面】

比例：{ratio}

風格：
高級商業商品攝影、
乾淨背景、
專業棚拍、
柔和電影級光線、
自然陰影、
高級電商視覺、
商品清晰對焦。

商品必須是畫面的視覺主體。

【禁止】

錯字、
亂碼、
虛假 Logo、
虛假品牌、
錯誤包裝、
變形商品、
多餘商品、
多餘配件、
錯誤文字、
不合理手指、
人體畸形、
低解析度、
過度 AI 感。

如果原圖無法確認某項資訊，
不要自行補充。
"""


# ============================================================
# 即夢影片 Prompt
# ============================================================

def generate_jimeng_video(data, seconds=15):

    name = data.get("name", "")
    points = data.get("points", "")

    if seconds == 15:
        timeline = """
0-3秒：
商品原圖建立第一視覺。
鏡頭緩慢推近。

3-6秒：
展示商品正面與主要細節。

6-9秒：
輕微環繞鏡頭。

9-12秒：
展示商品細節與質感。

12-15秒：
商品置中，留下乾淨品牌展示畫面。
"""

    elif seconds == 30:

        timeline = """
0-4秒：
商品英雄鏡頭。

4-9秒：
緩慢推近商品。

9-15秒：
展示商品細節。

15-21秒：
輕微環繞。

21-26秒：
展示包裝與整體外觀。

26-30秒：
商品置中完成收尾。
"""

    else:

        timeline = """
0-6秒：
商品英雄鏡頭。

6-15秒：
展示商品整體。

15-25秒：
展示細節。

25-35秒：
緩慢環繞商品。

35-45秒：
展示商品質感。

45-53秒：
商品完整展示。

53-60秒：
乾淨收尾。
"""

    return f"""
【即夢 AI 商品影片指令】

影片比例：9:16
影片長度：{seconds} 秒

商品：
{name}

已確認資訊：
{points}

【唯一商品來源】

上傳的商品原圖是唯一商品視覺來源。

必須保持：

品牌
Logo
包裝
商品形狀
顏色
材質
文字
標籤
結構

完全一致。

【鏡頭時間軸】

{timeline}

【攝影風格】

高級商業廣告攝影
電影級光線
自然景深
柔和陰影
慢速鏡頭
穩定運鏡
高級電商廣告質感

【禁止】

不要改品牌。
不要改 Logo。
不要改包裝。
不要生成新文字。
不要修改原有文字。
不要新增不存在的配件。
不要讓商品變形。
不要改變商品顏色。
不要改變商品材質。
不要虛構功能。
不要虛構規格。

如果資訊無法從原圖確認，
保持原樣，不要自行創造。
"""


# ============================================================
# AI 通用指令碼
# ============================================================

def generate_ai_command(data, target, task):

    context = product_context(data)

    return f"""
你現在是「黑金剛 AI 多 AI 總控中心」的專業 AI 執行代理。

你的目標：
{task}

指定 AI：
{target}

請依照以下商品資料工作：

{context}

==================================================
【黑金剛最高優先級規則】
==================================================

你只能使用：

1. 使用者提供的商品資料
2. 使用者提供的商品圖片
3. 已確認的商品資訊

禁止自行捏造：

品牌
型號
規格
容量
尺寸
材質
成分
功效
認證
產地
保固
包裝文字
價格
優惠
庫存
物流
任何不存在的資訊

無法確認時必須寫：

「無法確認，請人工確認」

==================================================
【執行任務】
==================================================

{task}

==================================================
【輸出格式】
==================================================

請使用繁體中文。

先提供：
① 商品分析

再提供：
② 核心賣點

再提供：
③ 行銷策略

再提供：
④ 實際可使用內容

最後提供：
⑤ 風險檢查

風險檢查必須確認：
- 是否有虛構資訊
- 是否有修改商品資訊
- 是否有誇大宣稱
- 是否有無法確認資料
"""


# ============================================================
# AI 平台
# ============================================================

AI_PLATFORMS = {

    "🦞 AI 龍蝦 / Agent": {
        "description": "AI Agent、任務拆解、自動化工作流",
        "url": "https://openclaw.ai/",
    },

    "🐋 DeepSeek": {
        "description": "推理、程式、文案、資料整理",
        "url": "https://chat.deepseek.com/",
    },

    "🟢 Gemini": {
        "description": "圖片理解、研究、文案",
        "url": "https://gemini.google.com/",
    },

    "🤖 ChatGPT": {
        "description": "企劃、文案、工作流程",
        "url": "https://chatgpt.com/",
    },

    "🟣 Claude": {
        "description": "長文、分析、整理",
        "url": "https://claude.ai/",
    },

    "⚡ Grok": {
        "description": "社群、趨勢、創意",
        "url": "https://grok.com/",
    },

    "🌐 Perplexity": {
        "description": "網路搜尋、資料研究",
        "url": "https://www.perplexity.ai/",
    },

    "🟠 Qwen": {
        "description": "中文、多模態、推理",
        "url": "https://chat.qwen.ai/",
    },

    "🌙 Kimi": {
        "description": "長文件、研究、Agent",
        "url": "https://www.kimi.com/",
    },

    "🟦 Copilot": {
        "description": "搜尋、文案、圖片",
        "url": "https://copilot.microsoft.com/",
    },
}


# ============================================================
# 登入頁
# ============================================================

def show_login():

    st.markdown(
        """
<div class="bk-hero">
<h1>🖤 黑金剛 AI 多 AI 總控中心 PRO</h1>
<p>一個商品資料，統一管理 Shopee、TikTok、即夢與多 AI。</p>
</div>
""",
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(
        ["🔐 登入", "📝 註冊"]
    )

    with tab1:

        username = st.text_input(
            "帳號",
            key="login_username",
        )

        password = st.text_input(
            "密碼",
            type="password",
            key="login_password",
        )

        if st.button(
            "🚀 登入黑金剛",
            use_container_width=True,
        ):

            ok, message = login_user(
                username,
                password,
            )

            if ok:

                st.success(message)
                st.rerun()

            else:

                st.error(message)

        st.info(
            "管理員測試帳號：admin / admin123"
        )

    with tab2:

        new_username = st.text_input(
            "新帳號",
            key="register_username",
        )

        new_password = st.text_input(
            "新密碼",
            type="password",
            key="register_password",
        )

        if st.button(
            "建立會員",
            use_container_width=True,
        ):

            ok, message = register_user(
                new_username,
                new_password,
            )

            if ok:
                st.success(message)
            else:
                st.error(message)


# ============================================================
# Sidebar
# ============================================================

def show_sidebar():

    with st.sidebar:

        st.markdown(
            "## 🖤 黑金剛"
        )

        st.caption(
            f"{APP_NAME}｜{APP_VERSION}"
        )

        st.divider()

        st.markdown(
            f"👤 **{st.session_state.user}**"
        )

        if st.session_state.role == "admin":
            st.markdown(
                '<span class="bk-tag">ADMIN</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span class="bk-tag">PRO MEMBER</span>',
                unsafe_allow_html=True,
            )

        st.divider()

        menu = st.radio(
            "控制中心",
            [
                "🏠 Dashboard",
                "🛒 蝦皮商品上架",
                "🧠 AI 指令碼中心",
                "🦞 AI 龍蝦",
                "🐋 DeepSeek",
                "🟢 Gemini",
                "🤖 ChatGPT",
                "🟣 Claude",
                "⚡ Grok",
                "🌐 Perplexity",
                "🟠 Qwen",
                "🌙 Kimi",
                "🟦 Copilot",
                "🎨 AI 圖片中心",
                "🎬 AI 影片中心",
                "🌙 即夢 AI",
                "🎵 TikTok 短影音",
                "📦 商品管理",
                "📚 AI 素材庫",
                "📜 歷史紀錄",
                "📊 數據分析",
                "💰 蝦皮分潤",
                "👑 管理中心",
            ],
        )

        st.divider()

        if st.button(
            "🚪 登出",
            use_container_width=True,
        ):

            st.session_state.logged_in = False
            st.session_state.user = ""
            st.session_state.role = "member"

            st.rerun()

    return menu


# ============================================================
# Header
# ============================================================

def page_header(title, subtitle=""):

    st.markdown(
        f"""
<div class="bk-hero">
<h1>{title}</h1>
<p>{subtitle}</p>
</div>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# Prompt 顯示工具
# ============================================================

def show_prompt(prompt, filename="ai_prompt.txt"):

    st.text_area(
        "AI 指令碼",
        value=prompt,
        height=520,
    )

    st.download_button(
        "⬇️ 下載指令碼",
        data=prompt,
        file_name=filename,
        mime="text/plain",
        use_container_width=True,
    )


# ============================================================
# Dashboard
# ============================================================

def page_dashboard():

    page_header(
        "🖤 黑金剛 AI 多 AI 總控中心",
        "一個商品資料，統一產生電商、短影音、圖片與多 AI 工作指令。",
    )

    products = load_json(
        PRODUCTS_FILE,
        [],
    )

    history = load_json(
        HISTORY_FILE,
        [],
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "📦 商品",
            len(products),
        )

    with c2:
        st.metric(
            "🧠 AI 任務",
            len(history),
        )

    with c3:
        st.metric(
            "🤖 AI 平台",
            len(AI_PLATFORMS),
        )

    with c4:
        st.metric(
            "🔑 API",
            "不需要",
        )

    st.markdown(
        "### 🚀 黑金剛工作流程"
    )

    cols = st.columns(4)

    workflow = [
        (
            "01",
            "📦",
            "建立商品",
            "輸入商品名稱、分類、賣點與原圖",
        ),
        (
            "02",
            "🧠",
            "AI 指令",
            "自動建立不同 AI 專用 Prompt",
        ),
        (
            "03",
            "🎨",
            "素材生成",
            "圖片、影片、即夢 Prompt",
        ),
        (
            "04",
            "🛒",
            "電商轉換",
            "Shopee + TikTok 行銷內容",
        ),
    ]

    for col, item in zip(cols, workflow):

        with col:

            st.markdown(
                f"""
<div class="bk-card">
<div class="bk-small">{item[0]}</div>
<div style="font-size:30px;">{item[1]}</div>
<div class="bk-title">{item[2]}</div>
<div class="bk-small">{item[3]}</div>
</div>
""",
                unsafe_allow_html=True,
            )

    st.markdown(
        "### 🤖 多 AI 總控"
    )

    ai_cols = st.columns(5)

    for index, (name, info) in enumerate(
        AI_PLATFORMS.items()
    ):

        with ai_cols[index % 5]:

            st.markdown(
                f"""
<div class="bk-card">
<div class="bk-title">{name}</div>
<div class="bk-small">{info["description"]}</div>
</div>
""",
                unsafe_allow_html=True,
            )

    st.markdown(
        "### 📦 最近商品"
    )

    if products:

        for product in products[:5]:

            st.markdown(
                f"""
<div class="bk-card">
<b>{product.get("name", "未命名商品")}</b><br>
<span class="bk-small">
{product.get("category", "其他")}
｜
NT$ {product.get("price", 0)}
｜
{product.get("created", "")}
</span>
</div>
""",
                unsafe_allow_html=True,
            )

    else:

        st.info(
            "目前還沒有商品，先到「蝦皮商品上架」建立第一個商品。"
        )


# ============================================================
# Shopee 商品上架
# ============================================================

def page_shopee():

    page_header(
        "🛒 蝦皮商品上架工作台",
        "商品資料一次建立，同時產生 Shopee、TikTok、即夢與 AI 指令。",
    )

    data = product_form(
        "shopee"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "💾 儲存商品",
            use_container_width=True,
        ):

            if not data["name"]:

                st.warning(
                    "請先輸入商品名稱。"
                )

            else:

                item = save_product(data)

                st.success(
                    f"商品「{item['name']}」已儲存。"
                )

                add_history(
                    "商品",
                    item["name"],
                    json.dumps(
                        item,
                        ensure_ascii=False,
                    ),
                )

    with col2:

        if st.button(
            "🧠 產生 Shopee 文案",
            use_container_width=True,
        ):

            if not data["name"]:

                st.warning(
                    "請先輸入商品名稱。"
                )

            else:

                copy = generate_shopee_copy(
                    data
                )

                show_prompt(
                    copy,
                    "shopee_copy.txt",
                )

                add_history(
                    "Shopee",
                    data["name"],
                    copy,
                )


# ============================================================
# AI 指令碼中心
# ============================================================

def page_ai_command_center():

    page_header(
        "🧠 AI 指令碼中心",
        "黑金剛的核心：同一份商品資料，轉換成不同 AI 可以直接執行的專用指令。",
    )

    products = load_json(
        PRODUCTS_FILE,
        [],
    )

    st.markdown(
        """
<div class="bk-card">
<b>🔥 第 3 部分已完整整合</b><br>
<span class="bk-small">
選擇商品 → 選擇 AI → 選擇任務 → 產生專用指令 → 複製到 AI。
</span>
</div>
""",
        unsafe_allow_html=True,
    )

    if products:

        product_names = [
            p.get("name", "未命名")
            for p in products
        ]

        selected_name = st.selectbox(
            "選擇已儲存商品",
            product_names,
            key="command_product",
        )

        data = next(
            (
                p
                for p in products
                if p.get("name") == selected_name
            ),
            {},
        )

        st.markdown(
            f"""
<div class="bk-card">
<div class="bk-title">
📦 {data.get("name", "")}
</div>
<span class="bk-tag">
{data.get("category", "其他")}
</span>
<span class="bk-tag">
NT$ {data.get("price", 0)}
</span>
<p class="bk-small">
{data.get("points", "")}
</p>
</div>
""",
            unsafe_allow_html=True,
        )

    else:

        st.info(
            "尚無商品。下面可以直接建立臨時商品資料。"
        )

        data = product_form(
            "command"
        )

    ai_name = st.selectbox(
        "選擇 AI",
        list(AI_PLATFORMS.keys()),
        key="command_ai",
    )

    task_options = [
        "分析商品並找出核心賣點",
        "產生蝦皮商品標題與描述",
        "產生 TikTok 短影音企劃",
        "產生社群行銷文案",
        "產生商品廣告文案",
        "分析競品與市場定位",
        "建立 AI Agent 自動化工作流程",
        "整理商品資訊",
        "建立完整電商行銷方案",
        "自訂任務",
    ]

    task_choice = st.selectbox(
        "任務",
        task_options,
        key="command_task",
    )

    custom_task = ""

    if task_choice == "自訂任務":

        custom_task = st.text_area(
            "自訂 AI 任務",
            placeholder="例如：幫我規劃這個商品的 7 天 TikTok 行銷內容",
            height=120,
            key="custom_ai_task",
        )

    task = (
        custom_task
        if task_choice == "自訂任務"
        else task_choice
    )

    if st.button(
        "⚡ 產生 AI 專用指令",
        use_container_width=True,
    ):

        if not data.get("name"):

            st.warning(
                "請先輸入商品名稱。"
            )

        elif not task.strip():

            st.warning(
                "請輸入任務。"
            )

        else:

            prompt = generate_ai_command(
                data,
                ai_name,
                task,
            )

            st.session_state.generated_prompt = prompt

            show_prompt(
                prompt,
                f"{safe_filename(ai_name)}_prompt.txt",
            )

            add_history(
                "AI指令",
                f"{ai_name}｜{data.get('name')}",
                prompt,
            )


# ============================================================
# 外部 AI 頁面
# ============================================================

def page_external_ai(platform_name):

    info = AI_PLATFORMS[platform_name]

    page_header(
        platform_name,
        info["description"],
    )

    st.link_button(
        f"🚀 開啟 {platform_name}",
        info["url"],
        use_container_width=True,
    )

    products = load_json(
        PRODUCTS_FILE,
        [],
    )

    if products:

        names = [
            p.get("name", "未命名")
            for p in products
        ]

        selected = st.selectbox(
            "選擇商品",
            names,
            key=f"external_{platform_name}",
        )

        data = next(
            (
                p
                for p in products
                if p.get("name") == selected
            ),
            {},
        )

    else:

        st.info(
            "還沒有商品，先建立一個臨時商品資料。"
        )

        data = product_form(
            safe_filename(platform_name)
        )

    task = st.text_area(
        "告訴 AI 要做什麼",
        value="分析商品並建立完整電商行銷方案",
        height=100,
        key=f"task_{platform_name}",
    )

    if st.button(
        "🧠 建立專用指令",
        use_container_width=True,
        key=f"generate_{platform_name}",
    ):

        prompt = generate_ai_command(
            data,
            platform_name,
            task,
        )

        show_prompt(
            prompt,
            f"{safe_filename(platform_name)}_prompt.txt",
        )

        add_history(
            "AI",
            f"{platform_name}｜{data.get('name', '')}",
            prompt,
        )


# ============================================================
# AI 圖片中心
# ============================================================

def page_image_center():

    page_header(
        "🎨 AI 圖片中心",
        "商品原圖 → 建立高一致性的 AI 商品圖片 Prompt。",
    )

    products = load_json(
        PRODUCTS_FILE,
        [],
    )

    if products:

        names = [
            p.get("name", "未命名")
            for p in products
        ]

        selected = st.selectbox(
            "選擇商品",
            names,
            key="image_product",
        )

        data = next(
            (
                p
                for p in products
                if p.get("name") == selected
            ),
            {},
        )

    else:

        data = product_form(
            "image"
        )

    ratio = st.selectbox(
        "圖片比例",
        [
            "1:1",
            "4:5",
            "9:16",
            "16:9",
        ],
        index=2,
    )

    if st.button(
        "🎨 產生 AI 圖片 Prompt",
        use_container_width=True,
    ):

        prompt = generate_jimeng_image(
            data,
            ratio,
        )

        show_prompt(
            prompt,
            "jimeng_image_prompt.txt",
        )

        add_history(
            "AI圖片",
            data.get("name", ""),
            prompt,
        )


# ============================================================
# AI 影片中心
# ============================================================

def page_video_center():

    page_header(
        "🎬 AI 影片中心",
        "建立商品短影音腳本與影片生成 Prompt。",
    )

    products = load_json(
        PRODUCTS_FILE,
        [],
    )

    if products:

        names = [
            p.get("name", "未命名")
            for p in products
        ]

        selected = st.selectbox(
            "選擇商品",
            names,
            key="video_product",
        )

        data = next(
            (
                p
                for p in products
                if p.get("name") == selected
            ),
            {},
        )

    else:

        data = product_form(
            "video"
        )

    seconds = st.selectbox(
        "影片長度",
        [15, 30, 60],
        key="video_seconds",
    )

    tab1, tab2 = st.tabs(
        [
            "🎬 影片腳本",
            "🌙 即夢影片 Prompt",
        ]
    )

    with tab1:

        if st.button(
            "📝 產生影片腳本",
            use_container_width=True,
        ):

            script = generate_tiktok(
                data,
                seconds,
            )

            show_prompt(
                script,
                "video_script.txt",
            )

            add_history(
                "影片腳本",
                data.get("name", ""),
                script,
            )

    with tab2:

        if st.button(
            "🎥 產生即夢影片 Prompt",
            use_container_width=True,
        ):

            prompt = generate_jimeng_video(
                data,
                seconds,
            )

            show_prompt(
                prompt,
                "jimeng_video_prompt.txt",
            )

            add_history(
                "即夢影片",
                data.get("name", ""),
                prompt,
            )


# ============================================================
# 即夢 AI
# ============================================================

def page_jimeng():

    page_header(
        "🌙 即夢 AI 中心",
        "專門處理商品圖片與 9:16 商品影片 Prompt。",
    )

    products = load_json(
        PRODUCTS_FILE,
        [],
    )

    if products:

        names = [
            p.get("name", "未命名")
            for p in products
        ]

        selected = st.selectbox(
            "選擇商品",
            names,
            key="jimeng_product",
        )

        data = next(
            (
                p
                for p in products
                if p.get("name") == selected
            ),
            {},
        )

    else:

        data = product_form(
            "jimeng"
        )

    tab1, tab2 = st.tabs(
        [
            "🎨 商品圖片",
            "🎬 商品影片",
        ]
    )

    with tab1:

        ratio = st.selectbox(
            "圖片比例",
            [
                "1:1",
                "4:5",
                "9:16",
                "16:9",
            ],
            key="jimeng_ratio",
        )

        if st.button(
            "🎨 建立即夢圖片指令",
            use_container_width=True,
        ):

            prompt = generate_jimeng_image(
                data,
                ratio,
            )

            show_prompt(
                prompt,
                "jimeng_image_prompt.txt",
            )

            add_history(
                "即夢圖片",
                data.get("name", ""),
                prompt,
            )

    with tab2:

        seconds = st.selectbox(
            "影片秒數",
            [15, 30, 60],
            key="jimeng_video_seconds",
        )

        if st.button(
            "🎬 建立即夢影片指令",
            use_container_width=True,
        ):

            prompt = generate_jimeng_video(
                data,
                seconds,
            )

            show_prompt(
                prompt,
                "jimeng_video_prompt.txt",
            )

            add_history(
                "即夢影片",
                data.get("name", ""),
                prompt,
            )


# ============================================================
# TikTok
# ============================================================

def page_tiktok():

    page_header(
        "🎵 TikTok 短影音中心",
        "商品資料直接轉換成 15 / 30 / 60 秒短影音腳本。",
    )

    products = load_json(
        PRODUCTS_FILE,
        [],
    )

    if products:

        names = [
            p.get("name", "未命名")
            for p in products
        ]

        selected = st.selectbox(
            "商品",
            names,
            key="tiktok_product",
        )

        data = next(
            (
                p
                for p in products
                if p.get("name") == selected
            ),
            {},
        )

    else:

        data = product_form(
            "tiktok"
        )

    seconds = st.selectbox(
        "影片長度",
        [15, 30, 60],
        key="tiktok_length",
    )

    if st.button(
        "🎵 產生 TikTok 腳本",
        use_container_width=True,
    ):

        script = generate_tiktok(
            data,
            seconds,
        )

        show_prompt(
            script,
            f"tiktok_{seconds}s_script.txt",
        )

        add_history(
            "TikTok",
            data.get("name", ""),
            script,
        )


# ============================================================
# 商品管理
# ============================================================

def page_products():

    page_header(
        "📦 商品管理",
        "管理已建立的商品資料。",
    )

    products = load_json(
        PRODUCTS_FILE,
        [],
    )

    st.metric(
        "目前商品數",
        len(products),
    )

    if not products:

        st.info(
            "目前沒有商品。"
        )

        return

    for product in products:

        with st.expander(
            f"📦 {product.get('name', '未命名')}｜{product.get('category', '其他')}"
        ):

            c1, c2 = st.columns(2)

            with c1:

                st.write(
                    f"**售價：** NT$ {product.get('price', 0)}"
                )

                st.write(
                    f"**分類：** {product.get('category', '')}"
                )

                st.write(
                    f"**建立時間：** {product.get('created', '')}"
                )

            with c2:

                image_path = product.get(
                    "image_path",
                    "",
                )

                if image_path and Path(
                    image_path
                ).exists():

                    st.image(
                        image_path,
                        width=180,
                    )

            st.write(
                product.get(
                    "points",
                    "",
                )
            )

            if st.button(
                "🗑️ 刪除商品",
                key=f"delete_{product.get('id')}",
            ):

                delete_product(
                    product.get("id")
                )

                st.success(
                    "商品已刪除"
                )

                st.rerun()


# ============================================================
# AI 素材庫
# ============================================================

def page_materials():

    page_header(
        "📚 AI 素材庫",
        "集中管理商品原圖與系統產生的素材。",
    )

    files = list(
        MEDIA_DIR.glob("*")
    )

    if not files:

        st.info(
            "目前沒有圖片素材。"
        )

        return

    st.write(
        f"目前共有 {len(files)} 個素材。"
    )

    cols = st.columns(4)

    for index, path in enumerate(files):

        with cols[index % 4]:

            if path.suffix.lower() in [
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
            ]:

                try:

                    st.image(
                        str(path),
                        width=180,
                    )

                except Exception:
                    pass

            st.caption(
                path.name
            )


# ============================================================
# 歷史紀錄
# ============================================================

def page_history():

    page_header(
        "📜 歷史紀錄",
        "查看黑金剛 AI 產生過的工作內容。",
    )

    history = load_json(
        HISTORY_FILE,
        [],
    )

    if not history:

        st.info(
            "目前沒有歷史紀錄。"
        )

        return

    kinds = sorted(
        set(
            h.get("kind", "其他")
            for h in history
        )
    )

    selected_kind = st.selectbox(
        "篩選類型",
        ["全部"] + kinds,
    )

    filtered = history

    if selected_kind != "全部":

        filtered = [
            h
            for h in history
            if h.get("kind") == selected_kind
        ]

    for item in filtered[:100]:

        with st.expander(
            f"{item.get('kind', '')}｜{item.get('title', '')}｜{item.get('time', '')}"
        ):

            content = item.get(
                "content",
                "",
            )

            st.text_area(
                "內容",
                value=content,
                height=300,
                key=f"history_{item.get('id')}",
            )


# ============================================================
# 數據分析
# ============================================================

def page_analytics():

    page_header(
        "📊 數據分析",
        "查看商品與 AI 工作量。",
    )

    products = load_json(
        PRODUCTS_FILE,
        [],
    )

    history = load_json(
        HISTORY_FILE,
        [],
    )

    category_count = {}

    for product in products:

        category = product.get(
            "category",
            "其他",
        )

        category_count[category] = (
            category_count.get(
                category,
                0,
            )
            + 1
        )

    kind_count = {}

    for item in history:

        kind = item.get(
            "kind",
            "其他",
        )

        kind_count[kind] = (
            kind_count.get(
                kind,
                0,
            )
            + 1
        )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "商品總數",
            len(products),
        )

    with c2:
        st.metric(
            "AI 工作數",
            len(history),
        )

    with c3:
        st.metric(
            "商品分類",
            len(category_count),
        )

    st.markdown(
        "### 📦 商品分類"
    )

    for category, count in sorted(
        category_count.items(),
        key=lambda x: x[1],
        reverse=True,
    ):

        st.write(
            f"**{category}**：{count} 個"
        )

    st.markdown(
        "### 🧠 AI 工作類型"
    )

    for kind, count in sorted(
        kind_count.items(),
        key=lambda x: x[1],
        reverse=True,
    ):

        st.write(
            f"**{kind}**：{count} 次"
        )


# ============================================================
# 蝦皮分潤
# ============================================================

def page_commission():

    page_header(
        "💰 蝦皮分潤計算中心",
        "快速計算售價、成本、平台費與預估淨利。",
    )

    c1, c2 = st.columns(2)

    with c1:

        sales = st.number_input(
            "商品售價",
            min_value=0.0,
            value=999.0,
            step=10.0,
        )

        cost = st.number_input(
            "商品成本",
            min_value=0.0,
            value=400.0,
            step=10.0,
        )

    with c2:

        commission = st.number_input(
            "平台／分潤比例 %",
            min_value=0.0,
            max_value=100.0,
            value=10.0,
            step=0.5,
        )

        other_fee = st.number_input(
            "其他固定費用",
            min_value=0.0,
            value=0.0,
            step=10.0,
        )

    fee = sales * commission / 100

    profit = sales - cost - fee - other_fee

    margin = (
        profit / sales * 100
        if sales > 0
        else 0
    )

    a, b, c = st.columns(3)

    with a:
        st.metric(
            "平台／分潤費",
            f"NT$ {fee:,.0f}",
        )

    with b:
        st.metric(
            "預估淨利",
            f"NT$ {profit:,.0f}",
        )

    with c:
        st.metric(
            "預估利潤率",
            f"{margin:.1f}%",
        )

    if st.button(
        "💾 保存計算結果",
        use_container_width=True,
    ):

        result = f"""
售價：NT$ {sales:,.0f}
成本：NT$ {cost:,.0f}
平台／分潤比例：{commission:.1f}%
平台／分潤費：NT$ {fee:,.0f}
其他費用：NT$ {other_fee:,.0f}
預估淨利：NT$ {profit:,.0f}
預估利潤率：{margin:.1f}%
"""

        add_history(
            "蝦皮分潤",
            "分潤計算",
            result,
        )

        st.success(
            "計算結果已保存。"
        )


# ============================================================
# 管理中心
# ============================================================

def page_admin():

    page_header(
        "👑 管理中心",
        "會員、期限與系統資料管理。",
    )

    if st.session_state.role != "admin":

        st.error(
            "只有管理員可以使用管理中心。"
        )

        return

    members = load_json(
        MEMBERS_FILE,
        {},
    )

    st.metric(
        "會員總數",
        len(members),
    )

    st.markdown(
        "### 👥 會員管理"
    )

    for username, member in list(
        members.items()
    ):

        st.markdown(
            f"""
<div class="bk-card">
<b>{username}</b>
｜
{member.get('role', 'member')}
｜
到期日：{member.get('expires', '')}
</div>
""",
            unsafe_allow_html=True,
        )

        if username != ADMIN_USERNAME:

            c1, c2 = st.columns(2)

            with c1:

                new_date = st.date_input(
                    "修改到期日",
                    value=datetime.fromisoformat(
                        member.get(
                            "expires",
                            date.today().isoformat(),
                        )
                    ).date(),
                    key=f"date_{username}",
                )

            with c2:

                if st.button(
                    "💾 更新期限",
                    key=f"update_{username}",
                    use_container_width=True,
                ):

                    members[username][
                        "expires"
                    ] = new_date.isoformat()

                    save_json(
                        MEMBERS_FILE,
                        members,
                    )

                    st.success(
                        f"{username} 期限已更新。"
                    )

                    st.rerun()


# ============================================================
# 登出後不可進入
# ============================================================

def require_login():

    if not st.session_state.logged_in:

        show_login()

        return False

    return True


# ============================================================
# Router
# ============================================================

def main():

    if not require_login():
        return

    menu = show_sidebar()

    if menu == "🏠 Dashboard":

        page_dashboard()

    elif menu == "🛒 蝦皮商品上架":

        page_shopee()

    elif menu == "🧠 AI 指令碼中心":

        page_ai_command_center()

    elif menu == "🦞 AI 龍蝦":

        page_external_ai(
            "🦞 AI 龍蝦 / Agent"
        )

    elif menu == "🐋 DeepSeek":

        page_external_ai(
            "🐋 DeepSeek"
        )

    elif menu == "🟢 Gemini":

        page_external_ai(
            "🟢 Gemini"
        )

    elif menu == "🤖 ChatGPT":

        page_external_ai(
            "🤖 ChatGPT"
        )

    elif menu == "🟣 Claude":

        page_external_ai(
            "🟣 Claude"
        )

    elif menu == "⚡ Grok":

        page_external_ai(
            "⚡ Grok"
        )

    elif menu == "🌐 Perplexity":

        page_external_ai(
            "🌐 Perplexity"
        )

    elif menu == "🟠 Qwen":

        page_external_ai(
            "🟠 Qwen"
        )

    elif menu == "🌙 Kimi":

        page_external_ai(
            "🌙 Kimi"
        )

    elif menu == "🟦 Copilot":

        page_external_ai(
            "🟦 Copilot"
        )

    elif menu == "🎨 AI 圖片中心":

        page_image_center()

    elif menu == "🎬 AI 影片中心":

        page_video_center()

    elif menu == "🌙 即夢 AI":

        page_jimeng()

    elif menu == "🎵 TikTok 短影音":

        page_tiktok()

    elif menu == "📦 商品管理":

        page_products()

    elif menu == "📚 AI 素材庫":

        page_materials()

    elif menu == "📜 歷史紀錄":

        page_history()

    elif menu == "📊 數據分析":

        page_analytics()

    elif menu == "💰 蝦皮分潤":

        page_commission()

    elif menu == "👑 管理中心":

        page_admin()


# ============================================================
# 程式入口
# ============================================================

if __name__ == "__main__":
    main()
