# ============================================================
# 黑金剛 AI 多 AI 總控中心 PRO
# VERSION 3.0 NO-API
# 手機相簿穩定整合版
# ============================================================

import io
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


# ============================================================
# 建立資料夾
# ============================================================

DATA_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Streamlit 設定
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
        radial-gradient(circle at top right, rgba(255, 193, 7, 0.08), transparent 30%),
        radial-gradient(circle at bottom left, rgba(255, 193, 7, 0.05), transparent 30%),
        #090909;
    color: #f5f5f5;
}

section[data-testid="stSidebar"] {
    background: #0d0d0d;
    border-right: 1px solid rgba(255, 193, 7, 0.18);
}

.bk-hero {
    padding: 28px;
    border-radius: 20px;
    background:
        linear-gradient(135deg, #171717, #0c0c0c);
    border: 1px solid rgba(255, 193, 7, 0.25);
    box-shadow: 0 10px 35px rgba(0,0,0,.35);
    margin-bottom: 22px;
}

.bk-title {
    font-size: 24px;
    font-weight: 800;
    margin-bottom: 12px;
}

.bk-subtitle {
    color: #bbbbbb;
    font-size: 14px;
    line-height: 1.7;
}

.bk-card {
    padding: 20px;
    border-radius: 18px;
    background: rgba(22,22,22,.92);
    border: 1px solid rgba(255,193,7,.16);
    margin-bottom: 18px;
}

.bk-big {
    font-size: 34px;
    font-weight: 900;
}

.bk-small {
    color: #999;
    font-size: 13px;
}

.bk-tag {
    display: inline-block;
    padding: 5px 11px;
    border-radius: 999px;
    background: rgba(255,193,7,.10);
    color: #ffc107;
    border: 1px solid rgba(255,193,7,.25);
    font-size: 12px;
    margin-right: 5px;
}

.bk-success {
    padding: 12px 15px;
    border-radius: 12px;
    background: rgba(0, 200, 120, .08);
    border: 1px solid rgba(0, 200, 120, .20);
}

.bk-warning {
    padding: 12px 15px;
    border-radius: 12px;
    background: rgba(255, 193, 7, .08);
    border: 1px solid rgba(255, 193, 7, .20);
}

.bk-danger {
    padding: 12px 15px;
    border-radius: 12px;
    background: rgba(255, 60, 60, .08);
    border: 1px solid rgba(255, 60, 60, .20);
}

div[data-testid="stMetric"] {
    background: #141414;
    border: 1px solid rgba(255,193,7,.12);
    padding: 12px;
    border-radius: 14px;
}

.stButton > button {
    border-radius: 12px;
    min-height: 42px;
    font-weight: 700;
}

.stDownloadButton > button {
    border-radius: 12px;
    font-weight: 700;
}

textarea {
    line-height: 1.65 !important;
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
# 安全工具
# ============================================================

def hash_password(password):
    return hashlib.sha256(
        str(password).encode("utf-8")
    ).hexdigest()


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
# Session State
# ============================================================

DEFAULT_SESSION = {
    "logged_in": False,
    "user": "",
    "role": "member",
    "page": "Dashboard",
    "last_product": {},
    "generated_prompt": "",
    "gemini_model": "",
    "gemini_error": "",
}

for key, value in DEFAULT_SESSION.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# 會員
# ============================================================

def is_expired(member):

    if member.get("role") == "admin":
        return False

    expires = member.get("expires", "")

    if not expires:
        return True

    try:
        expire_date = datetime.strptime(
            expires,
            "%Y-%m-%d",
        ).date()

        return date.today() > expire_date

    except Exception:
        return True


def login_user(username, password):

    members = load_json(MEMBERS_FILE, {})

    if username not in members:
        return False, "帳號不存在"

    member = members[username]

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
        return False, "帳號至少 3 個字"

    if len(password) < 6:
        return False, "密碼至少 6 個字"

    members = load_json(MEMBERS_FILE, {})

    if username in members:
        return False, "帳號已存在"

    expire_date = date.today() + timedelta(
        days=DEFAULT_MEMBER_DAYS
    )

    members[username] = {
        "password": hash_password(password),
        "role": "member",
        "expires": expire_date.strftime("%Y-%m-%d"),
        "created": datetime.now().isoformat(),
    }

    if not save_json(MEMBERS_FILE, members):
        return False, "會員資料保存失敗"

    return True, "註冊成功"


# ============================================================
# 歷史紀錄
# ============================================================

def add_history(kind, title, content):

    history = load_json(HISTORY_FILE, [])

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

    item = {
        "name": data.get(
            "name",
            "",
        ),
        "category": data.get(
            "category",
            "其他",
        ),
        "price": int(
            data.get(
                "price",
                0,
            )
        ),
        "points": data.get(
            "points",
            "",
        ),
        "seconds": int(
            data.get(
                "seconds",
                15,
            )
        ),
        "image_path": "",
        "image_name": data.get(
            "image_name",
            "",
        ),
        "id": secrets.token_hex(8),
        "created": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "user": st.session_state.get(
            "user",
            "",
        ),
    }

    # ========================================================
    # 重要：
    # 只有使用者按「儲存商品」後才真正處理圖片
    # 不在 file_uploader rerun 時寫檔
    # ========================================================

    image_bytes = data.get(
        "image_bytes",
        b"",
    )

    if image_bytes:

        try:

            if len(image_bytes) <= MAX_IMAGE_MB * 1024 * 1024:

                image = Image.open(
                    io.BytesIO(image_bytes)
                )

                image = ImageOps.exif_transpose(
                    image
                )

                if (
                    image.width > MAX_IMAGE_SIZE
                    or image.height > MAX_IMAGE_SIZE
                ):
                    image.thumbnail(
                        (
                            MAX_IMAGE_SIZE,
                            MAX_IMAGE_SIZE,
                        )
                    )

                if image.mode != "RGB":
                    image = image.convert("RGB")

                filename = (
                    safe_filename(
                        item["name"]
                        or "product"
                    )
                    + "_"
                    + datetime.now().strftime(
                        "%Y%m%d%H%M%S"
                    )
                    + "_"
                    + secrets.token_hex(3)
                    + ".jpg"
                )

                image_path = MEDIA_DIR / filename

                image.save(
                    image_path,
                    "JPEG",
                    quality=90,
                    optimize=True,
                )

                item["image_path"] = str(
                    image_path
                )

        except Exception:
            item["image_path"] = ""

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

    if not isinstance(products, list):
        products = []

    new_products = [
        p
        for p in products
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
            "果乾",
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
            "美容",
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
            "usb",
        ],

        "居家生活": [
            "清潔",
            "收納",
            "杯",
            "鍋",
            "家居",
            "居家",
            "用品",
            "廚房",
        ],

        "服飾": [
            "衣",
            "褲",
            "鞋",
            "襪",
            "包",
            "帽",
            "服飾",
            "外套",
        ],

        "汽機車": [
            "汽車",
            "機車",
            "車用",
            "行車記錄器",
            "輪胎",
            "汽配",
        ],
    }

    for category, words in categories.items():

        for word in words:

            if word in text:
                return category

    return "其他"


# ============================================================
# 手機相簿穩定版商品表單
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
        placeholder=(
            "例如：甘草芭樂、UNO洗面乳、藍牙耳機"
        ),
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
            "輸入已確認的商品資訊。\n"
            "例如：容量、材質、功能、口味、尺寸、特色等。\n"
            "沒有資料的部分，AI 不得自行編造。"
        ),
        height=140,
        key=f"{prefix}_points",
    )

    st.markdown(
        "### 📷 商品原圖"
    )

    st.caption(
        "手機／平板點擊下面按鈕後，可選擇相簿中的照片。"
    )

    # ========================================================
    # 核心穩定設定
    #
    # 不使用 capture
    # 不立即寫入 MEDIA_DIR
    # 不立即轉 JPG
    # 不立即 resize
    # ========================================================

    uploaded = st.file_uploader(
        "選擇商品照片",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
        ],
        accept_multiple_files=False,
        key=f"{prefix}_image",
        help="手機可從照片／相簿選擇商品圖片。",
    )

    image_bytes = b""
    image_name = ""

    if uploaded is not None:

        try:

            raw = uploaded.getvalue()

            if len(raw) > MAX_IMAGE_MB * 1024 * 1024:

                st.error(
                    f"圖片太大："
                    f"{len(raw) / 1024 / 1024:.1f} MB。"
                    f"請選擇 {MAX_IMAGE_MB} MB 以下的照片。"
                )

            else:

                image_bytes = raw
                image_name = uploaded.name

                st.markdown(
                    "#### 🖼️ 已選擇商品照片"
                )

                # =================================================
                # 這裡只預覽，不保存檔案
                # =================================================

                st.image(
                    image_bytes,
                    width=320,
                )

                st.success(
                    f"已選擇：{image_name}"
                )

                st.caption(
                    "圖片目前只存在本次操作中；"
                    "按「💾 儲存商品」後才會保存到商品資料。"
                )

        except Exception:

            image_bytes = b""
            image_name = ""

            st.error(
                "圖片讀取失敗，請重新選擇照片。"
            )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    return {
        "name": name.strip(),
        "category": category,
        "price": int(price),
        "points": points.strip(),
        "seconds": int(seconds),
        "image_bytes": image_bytes,
        "image_name": image_name,
    }


# ============================================================
# 商品上下文
# ============================================================

def product_context(data):

    name = data.get(
        "name",
        "",
    )

    category = data.get(
        "category",
        "其他",
    )

    price = data.get(
        "price",
        0,
    )

    points = data.get(
        "points",
        "",
    )

    image_name = data.get(
        "image_name",
        "",
    )

    return f"""
【商品資料】

商品名稱：
{name or "未提供"}

商品分類：
{category}

商品售價：
{price}

已確認商品賣點：
{points or "未提供"}

商品原圖：
{image_name or "未提供"}

【最高優先級規則】

1. 只能使用使用者提供的商品資料。
2. 商品圖片是唯一視覺來源。
3. 不得自行編造品牌。
4. 不得自行編造型號。
5. 不得自行編造容量。
6. 不得自行編造尺寸。
7. 不得自行編造材質。
8. 不得自行編造功能。
9. 不得自行編造功效。
10. 不得自行編造認證。
11. 不得自行編造產地。
12. 不得自行編造保固。
13. 不得自行編造包裝文字。
14. 不得自行編造價格。
15. 不得自行編造折扣。
16. 不得自行編造庫存。
17. 不得自行編造物流資訊。
18. 不得自行編造「熱賣」「人氣」「限時優惠」等事實。
19. 圖片看不到的資訊不得自行猜測。
20. 無法確認的內容必須標示：
   「無法確認，請人工確認」。

【圖片一致性】

如果需要產生圖片或影片 Prompt：

- 商品外型保持一致
- 顏色保持一致
- 包裝保持一致
- 品牌保持一致
- Logo 保持一致
- 商品文字保持一致
- 標籤保持一致
- 不增加不存在的配件
- 不改變商品結構
- 不重新設計包裝
"""


# ============================================================
# Shopee 文案
# ============================================================

def generate_shopee_copy(data):

    name = data.get(
        "name",
        "",
    )

    category = data.get(
        "category",
        "其他",
    )

    points = data.get(
        "points",
        "",
    )

    confirmed_points = (
        points
        if points
        else "請依商品實際資訊補充"
    )

    title_1 = (
        f"{name}｜{category}｜商品介紹"
        if name
        else f"{category}｜商品介紹"
    )

    title_2 = (
        f"{name}｜{category}｜特色整理"
        if name
        else f"{category}｜特色整理"
    )

    title_3 = (
        f"{name}｜{category}｜商品資訊"
        if name
        else f"{category}｜商品資訊"
    )

    keywords = [
        name,
        category,
    ]

    if points:

        for part in re.split(
            r"[,，、\n]",
            points,
        ):

            part = part.strip()

            if part:
                keywords.append(part[:20])

    keywords = [
        x
        for x in keywords
        if x
    ]

    keyword_text = "、".join(
        dict.fromkeys(keywords)
    )

    return f"""
# 🛒 蝦皮商品上架文案

## 一、商品標題候選

1. {title_1}
2. {title_2}
3. {title_3}

## 二、商品分類

{category}

## 三、商品已確認資訊

{confirmed_points}

## 四、商品介紹

商品名稱：{name or "未提供"}

本商品介紹內容只根據目前提供的商品資訊整理。
沒有提供的規格、功能、品牌、產地、容量、尺寸或功效，
不得自行補充。

## 五、關鍵字方向

{keyword_text or "請人工確認關鍵字"}

## 六、上架前人工確認

□ 品牌
□ 型號
□ 規格
□ 尺寸
□ 容量
□ 材質
□ 產地
□ 保固
□ 商品圖片
□ 商品價格
□ 庫存
□ 物流
□ 促銷活動

⚠️ 以上未確認項目不可直接當成商品事實。
"""


# ============================================================
# TikTok 腳本
# ============================================================

def generate_tiktok(data):
