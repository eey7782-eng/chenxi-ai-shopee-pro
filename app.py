# ============================================================
# 黑金剛 AI 蝦皮半自動化 2.5 PRO
# Stable Edition
# Streamlit Cloud / 手機 / 平板
# ============================================================

import os
import io
import json
import base64
import hashlib
import re
from pathlib import Path
from datetime import datetime, date, timedelta

import streamlit as st
from PIL import Image, ImageOps


# ============================================================
# 基本設定
# ============================================================

APP_NAME = "黑金剛 AI 蝦皮半自動化 2.5 PRO"
APP_VERSION = "5.0-STABLE"

DATA_DIR = Path("data")
MEMBER_FILE = DATA_DIR / "members.json"
PRODUCT_DIR = DATA_DIR / "products"
HISTORY_DIR = DATA_DIR / "history"
MEDIA_DIR = DATA_DIR / "media"

for folder in [
    DATA_DIR,
    PRODUCT_DIR,
    HISTORY_DIR,
    MEDIA_DIR,
]:
    folder.mkdir(parents=True, exist_ok=True)


MAX_IMAGE_MB = 20
MAX_IMAGE_SIZE = 1600

MAX_VIDEO_MB = 300

SUPPORTED_IMAGES = [
    "jpg",
    "jpeg",
    "png",
    "webp",
]

SUPPORTED_VIDEOS = [
    "mp4",
    "mov",
    "webm",
]


# ============================================================
# Streamlit
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🥷",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Session State
# ============================================================

DEFAULT_STATE = {
    "logged_in": False,
    "username": "",
    "is_admin": False,
    "member_expires": None,
    "page": "Dashboard",

    "current_product": {},
    "image_bytes": None,
    "image_name": "",
    "image_mime": "image/jpeg",

    "video_bytes": None,
    "video_name": "",
    "video_mime": "video/mp4",

    "analysis_result": "",
    "shopee_result": "",
    "tiktok_result": "",
    "jimeng_result": "",

    "gemini_model": "",
    "gemini_error": "",
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background: #090909;
    color: #ffffff;
}

.block-container {
    max-width: 1500px;
    padding-top: 1rem;
    padding-bottom: 3rem;
}

.hero {
    background: linear-gradient(135deg, #151515, #0d0d0d);
    border: 1px solid #303030;
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 20px;
}

.hero-title {
    font-size: 30px;
    font-weight: 900;
}

.hero-sub {
    color: #999999;
    margin-top: 8px;
}

.card {
    background: #141414;
    border: 1px solid #2d2d2d;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 16px;
}

.step-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 10px;
    margin: 15px 0;
}

.step {
    background: #151515;
    border: 1px solid #303030;
    border-radius: 14px;
    padding: 16px 8px;
    text-align: center;
}

.step-number {
    font-size: 20px;
    font-weight: 900;
}

.step-title {
    font-size: 13px;
    color: #dddddd;
    margin-top: 5px;
}

.small-text {
    color: #999999;
    font-size: 13px;
}

.login-box {
    max-width: 900px;
    margin: 30px auto;
}

.warning-box {
    background: #211b0a;
    border: 1px solid #6d5716;
    border-radius: 12px;
    padding: 14px;
}

@media (max-width: 900px) {

    .step-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .hero-title {
        font-size: 23px;
    }

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

        text = path.read_text(encoding="utf-8")

        if not text.strip():
            return default

        return json.loads(text)

    except Exception:
        return default


def save_json(path, data):
    path = Path(path)

    temp_path = path.with_suffix(path.suffix + ".tmp")

    temp_path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    temp_path.replace(path)


# ============================================================
# 安全雜湊
# ============================================================

def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# ============================================================
# 使用者名稱標準化
# ============================================================

def normalize_username(username):
    return (username or "").strip().lower()


# ============================================================
# 會員資料
# ============================================================

def get_members():
    data = load_json(MEMBER_FILE, {})

    if not isinstance(data, dict):
        return {}

    return data


def create_default_admin():
    members = get_members()

    if "admin" not in members:

        members["admin"] = {
            "password_hash": hash_password("admin123"),
            "expires": None,
            "admin": True,
            "created": datetime.now().isoformat(),
        }

        save_json(MEMBER_FILE, members)


create_default_admin()


# ============================================================
# 會員登入
# ============================================================

def check_member_expiration(member):
    expires = member.get("expires")

    if not expires:
        return True, ""

    try:
        expire_date = date.fromisoformat(str(expires))

    except Exception:
        return False, "會員資料的到期日期格式錯誤"

    if date.today() > expire_date:
        return False, "會員已到期"

    return True, ""


def login_user(username, password):

    username = normalize_username(username)

    if not username:
        return False, "請輸入帳號"

    if not password:
        return False, "請輸入密碼"

    members = get_members()

    member = members.get(username)

    if member is None:
        return False, "帳號不存在"

    stored_hash = member.get("password_hash", "")

    if stored_hash != hash_password(password):
        return False, "密碼錯誤"

    active, message = check_member_expiration(member)

    if not active:
        return False, message

    st.session_state.logged_in = True
    st.session_state.username = username
    st.session_state.is_admin = bool(member.get("admin", False))
    st.session_state.member_expires = member.get("expires")

    return True, "登入成功"


# ============================================================
# 註冊
# ============================================================

def register_user(username, password, password_confirm):

    username = normalize_username(username)

    if not re.fullmatch(
        r"[a-z0-9_.-]{3,30}",
        username,
    ):
        return (
            False,
            "帳號需 3～30 碼，只能使用英文、數字、_、.、-",
        )

    if len(password) < 6:
        return False, "密碼至少需要 6 碼"

    if password != password_confirm:
        return False, "兩次輸入的密碼不一致"

    members = get_members()

    if username in members:
        return False, "這個帳號已經存在"

    expire_date = date.today() + timedelta(days=30)

    members[username] = {
        "password_hash": hash_password(password),
        "expires": expire_date.isoformat(),
        "admin": False,
        "created": datetime.now().isoformat(),
    }

    try:
        save_json(MEMBER_FILE, members)

    except Exception as error:
        return False, f"會員資料無法保存：{error}"

    return (
        True,
        f"註冊成功！會員有效期限至 {expire_date.isoformat()}",
    )


# ============================================================
# 登出
# ============================================================

def logout():

    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.is_admin = False
    st.session_state.member_expires = None

    st.session_state.current_product = {}
    st.session_state.image_bytes = None
    st.session_state.video_bytes = None

    st.session_state.analysis_result = ""
    st.session_state.shopee_result = ""
    st.session_state.tiktok_result = ""
    st.session_state.jimeng_result = ""

    st.rerun()


# ============================================================
# Gemini
# ============================================================

try:

    from google import genai

    HAS_GENAI = True

except Exception:

    genai = None
    HAS_GENAI = False


GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
]


def get_secret(name):

    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""

    if not value:
        value = os.getenv(name, "")

    return str(value or "").strip()


@st.cache_resource
def get_gemini_client(api_key):

    if not api_key:
        return None

    if not HAS_GENAI:
        return None

    try:
        return genai.Client(
            api_key=api_key
        )

    except Exception:
        return None


def call_gemini(prompt, image_bytes=None, image_mime="image/jpeg"):

    api_key = get_secret("GEMINI_API_KEY")

    if not api_key:

        st.session_state.gemini_error = (
            "尚未設定 GEMINI_API_KEY"
        )

        return None

    client = get_gemini_client(api_key)

    if client is None:

        st.session_state.gemini_error = (
            "Gemini Client 無法建立，請確認 google-genai "
            "與 GEMINI_API_KEY。"
        )

        return None

    if image_bytes:

        image_part = {
            "type": "image",
            "mime_type": image_mime,
            "data": base64.b64encode(
                image_bytes
            ).decode("utf-8"),
        }

        input_data = [
            image_part,
            {
                "type": "text",
                "text": prompt,
            },
        ]

    else:

        input_data = prompt

    last_error = ""

    for model in GEMINI_MODELS:

        try:

            response = client.interactions.create(
                model=model,
                input=input_data,
            )

            text = getattr(
                response,
                "output_text",
                None,
            )

            if text:

                st.session_state.gemini_model = model
                st.session_state.gemini_error = ""

                return text.strip()

        except Exception as error:

            last_error = str(error)

    st.session_state.gemini_error = (
        last_error or "Gemini 沒有回傳內容"
    )

    return None


# ============================================================
# 商品分類
# ============================================================

def detect_category(text):

    text = (text or "").lower()

    categories = {

        "食品": [
            "芭樂",
            "水果",
            "零食",
            "食品",
            "茶",
            "咖啡",
            "糖",
            "餅乾",
            "肉乾",
        ],

        "保養美妝": [
            "洗面",
            "乳液",
            "精華",
            "面膜",
            "保養",
            "彩妝",
            "口紅",
            "洗髮",
        ],

        "3C": [
            "手機",
            "平板",
            "耳機",
            "充電",
            "鍵盤",
            "滑鼠",
            "電腦",
            "充電器",
        ],

        "居家生活": [
            "收納",
            "清潔",
            "居家",
            "廚房",
            "杯",
            "鍋",
            "垃圾袋",
        ],

        "服飾": [
            "衣",
            "褲",
            "鞋",
            "襪",
            "外套",
            "包包",
            "帽",
        ],

        "汽機車": [
            "汽車",
            "機車",
            "車用",
            "雨刷",
            "機油",
        ],
    }

    for category_name, keywords in categories.items():

        for keyword in keywords:

            if keyword.lower() in text:
                return category_name

    return "其他"


# ============================================================
# AI 核心規則
# ============================================================

IMAGE_RULES = """
【黑金剛商品圖片最高優先規則】

1. 上傳商品圖片是商品外觀判斷的最高優先來源。
2. 必須保持原商品。
3. 不得自行修改品牌。
4. 不得自行修改 Logo。
5. 不得修改包裝。
6. 不得修改產品形狀。
7. 不得修改顏色。
8. 不得修改材質。
9. 不得自行新增圖片不存在的文字。
10. 不得虛構型號。
11. 不得虛構容量。
12. 不得虛構重量。
13. 不得虛構尺寸。
14. 不得虛構成分。
15. 不得虛構功效。
16. 不得虛構認證。
17. 不得虛構產地。
18. 不得虛構規格。
19. 不確定的資訊必須寫「圖片無法確認」。
20. 使用者資料與圖片衝突時，必須標示：
「⚠️ 商品資料與圖片可能不一致」。
21. 影片生成 Prompt 必須要求保持原商品外觀。
"""


# ============================================================
# AI Prompt
# ============================================================

def build_analysis_prompt(product):

    return f"""
你是「黑金剛 AI 蝦皮半自動化 2.5 PRO」商品視覺分析 AI。

請分析使用者提供的商品圖片。

商品名稱：
{product["name"]}

商品分類：
{product["category"]}

商品價格：
NT$ {product["price"]}

使用者提供的賣點：
{product["selling"]}

{IMAGE_RULES}

請使用繁體中文輸出：

【一、商品基本分析】
商品類型：
品牌：
Logo：
外觀：
主要顏色：
材質：
包裝：
圖片文字：

【二、圖片可確認資訊】
列出圖片真正可以確認的資訊。

【三、不可確認資訊】
所有無法從圖片確認的資訊請列出。

【四、商品賣點】
只能使用圖片與使用者明確提供的資訊。

【五、蝦皮 SEO 標題】
提供 3 個版本。

【六、蝦皮商品描述】
適合台灣蝦皮。

【七、短版銷售文案】

【八、TikTok Hook】
提供 3 個。

【九、TikTok 15 秒腳本】

【十、TikTok 30 秒腳本】

【十一、即夢 AI 2.5 商品影片 Prompt】
影片比例 9:16。
解析度 1080x1920。
15 秒。
必須保持原商品。

【十二、圖片與商品資料衝突檢查】

不要虛構任何商品資訊。
"""


def build_shopee_prompt(product, analysis):

    return f"""
你是台灣蝦皮電商文案專家。

商品名稱：
{product["name"]}

分類：
{product["category"]}

價格：
NT$ {product["price"]}

使用者賣點：
{product["selling"]}

AI 商品分析：
{analysis}

{IMAGE_RULES}

請產生：

1. 蝦皮 SEO 標題 3 組
2. 商品描述
3. 商品特色
4. 主要賣點
5. 使用情境
6. 注意事項
7. 短版銷售文案
8. 關鍵字
9. TikTok Hook
10. TikTok 15 秒腳本
11. TikTok 30 秒腳本

不得虛構圖片沒有的資訊。
"""


def build_tiktok_prompt(product, analysis):

    return f"""
你是台灣短影音電商內容專家。

商品：
{product["name"]}

分類：
{product["category"]}

商品分析：
{analysis}

{IMAGE_RULES}

請製作：

【TikTok 3 秒 Hook】
提供 5 個。

【15 秒影片】
0-3 秒：
3-6 秒：
6-10 秒：
10-13 秒：
13-15 秒：

【30 秒影片】
完整分鏡。

每個鏡頭包含：
畫面
動作
字幕
口播
音效
CTA

規格：
9:16
1080x1920

不得修改商品原始外觀。
"""


def build_jimeng_prompt(product, analysis):

    return f"""
你是「黑金剛」即夢 AI 2.5 商品影片 Prompt 專家。

商品名稱：
{product["name"]}

商品分析：
{analysis}

{IMAGE_RULES}

請建立一個完整的：

15 秒
9:16
1080x1920

高級商業商品廣告影片 Prompt。

時間軸：

0-3 秒：
建立乾淨高級場景。

3-6 秒：
慢速電影感推鏡。

6-9 秒：
輕微環繞商品。

9-12 秒：
商品細節特寫。

12-15 秒：
英雄鏡頭。

視覺要求：

高級商業攝影。
電影級燈光。
真實材質。
自然反射。
淺景深。
乾淨背景。
商品保持清晰。
慢速穩定鏡頭。
自然景深。

最重要：

必須以使用者上傳的商品圖片作為唯一商品外觀依據。

不得改變品牌。
不得改變 Logo。
不得改變包裝。
不得改變顏色。
不得改變形狀。
不得改變材質。
不得新增圖片不存在的文字。

只輸出完整影片 Prompt。
"""


# ============================================================
# 圖片處理
# ============================================================

def process_uploaded_image(uploaded_file):

    raw = uploaded_file.getvalue()

    if len(raw) > MAX_IMAGE_MB * 1024 * 1024:

        raise ValueError(
            f"圖片不可超過 {MAX_IMAGE_MB} MB"
        )

    image = Image.open(
        io.BytesIO(raw)
    )

    image = ImageOps.exif_transpose(image)

    image.thumbnail(
        (MAX_IMAGE_SIZE, MAX_IMAGE_SIZE)
    )

    output = io.BytesIO()

    image.convert("RGB").save(
        output,
        format="JPEG",
        quality=92,
        optimize=True,
    )

    return output.getvalue()


# ============================================================
# 儲存商品
# ============================================================

def create_product_id():

    return datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )


def save_product(product):

    product_id = product.get(
        "id",
        create_product_id(),
    )

    product["id"] = product_id

    product_path = PRODUCT_DIR / f"{product_id}.json"

    save_json(
        product_path,
        product,
    )

    return product_path


# ============================================================
# 儲存歷史
# ============================================================

def save_history(data):

    history_id = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    path = HISTORY_DIR / f"{history_id}.json"

    save_json(
        path,
        data,
    )


# ============================================================
# 商品指令碼圖
# ============================================================

def render_workflow():

    st.markdown(
        """
<div class="step-grid">

<div class="step">
<div class="step-number">01</div>
<div class="step-title">🖼️ 商品原圖</div>
</div>

<div class="step">
<div class="step-number">02</div>
<div class="step-title">🔍 Gemini 分析</div>
</div>

<div class="step">
<div class="step-number">03</div>
<div class="step-title">🧩 商品指令碼</div>
</div>

<div class="step">
<div class="step-number">04</div>
<div class="step-title">🛒 蝦皮上架</div>
</div>

<div class="step">
<div class="step-number">05</div>
<div class="step-title">🎵 TikTok</div>
</div>

<div class="step">
<div class="step-number">06</div>
<div class="step-title">🎬 即夢影片</div>
</div>

</div>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# 登入頁
# ============================================================

def login_page():

    st.markdown(
        f"""
<div class="login-box">

<div class="hero">

<div class="hero-title">
🥷 {APP_NAME}
</div>

<div class="hero-sub">
商品圖片 → AI分析 → 商品指令碼圖 → 蝦皮 → TikTok → 即夢 → 商品影片
</div>

</div>

</div>
""",
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)

    # --------------------------------------------------------
    # 登入
    # --------------------------------------------------------

    with left:

        st.subheader("🔐 會員登入")

        with st.form("login_form"):

            username = st.text_input(
                "帳號",
                placeholder="輸入你的帳號",
            )

            password = st.text_input(
                "密碼",
                type="password",
                placeholder="輸入密碼",
            )

            submitted = st.form_submit_button(
                "登入",
                type="primary",
                use_container_width=True,
            )

        if submitted:

            ok, message = login_user(
                username,
                password,
            )

            # 這裡故意不用：
            # st.success(message) if ok else st.error(message)
            #
            # 避免你之前遇到 DeltaGenerator 顯示問題。

            if ok:

                st.success(message)
                st.rerun()

            else:

                st.error(message)

    # --------------------------------------------------------
    # 註冊
    # --------------------------------------------------------

    with right:

        st.subheader("👤 註冊會員")

        with st.form("register_form"):

            new_username = st.text_input(
                "新帳號",
                placeholder="例如：shop001",
            )

            new_password = st.text_input(
                "新密碼",
                type="password",
                placeholder="至少 6 碼",
            )

            new_password_confirm = st.text_input(
                "再次輸入密碼",
                type="password",
            )

            register_submit = st.form_submit_button(
                "註冊帳號",
                use_container_width=True,
            )

        if register_submit:

            ok, message = register_user(
                new_username,
                new_password,
                new_password_confirm,
            )

            if ok:

                st.success(message)

                st.info(
                    "帳號已建立，請使用剛剛註冊的帳號登入。"
                )

            else:

                st.error(message)

    st.divider()

    st.markdown(
        """
<div class="warning-box">

<strong>第一次使用：</strong><br>
預設管理員帳號：admin<br>
預設管理員密碼：admin123

</div>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# 未登入
# ============================================================

if not st.session_state.logged_in:

    login_page()

    st.stop()


# =============================================
