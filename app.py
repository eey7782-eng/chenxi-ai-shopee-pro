import os
import io
import json
import base64
import hashlib
import hmac
import re
import secrets as py_secrets
from pathlib import Path
from datetime import datetime, date, timedelta

import streamlit as st
from PIL import Image, ImageOps


# ============================================================
# 基本設定
# ============================================================

APP_NAME = "黑金剛 AI 蝦皮半自動化 2.5 PRO"
APP_VERSION = "4.1"

DATA_DIR = Path("data")
HISTORY_DIR = DATA_DIR / "history"
PRODUCT_DIR = DATA_DIR / "products"
MEDIA_DIR = DATA_DIR / "media"
MEMBERS_FILE = DATA_DIR / "members.json"

for folder in (
    DATA_DIR,
    HISTORY_DIR,
    PRODUCT_DIR,
    MEDIA_DIR,
):
    folder.mkdir(parents=True, exist_ok=True)

MAX_IMAGE_MB = 20
MAX_VIDEO_MB = 300
MAX_IMAGE_SIZE = 1600

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
]


# ============================================================
# Gemini SDK
# ============================================================

try:
    from google import genai

    HAS_GENAI = True
except ImportError:
    genai = None
    HAS_GENAI = False


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
    "page": "Dashboard",
    "gemini_model": "",
    "gemini_error": "",
    "analysis_result": "",
    "shopee_result": "",
    "jimeng_result": "",
    "tiktok_result": "",
    "current_product": {},
    "image_bytes": None,
    "image_mime": "image/jpeg",
    "video_bytes": None,
    "video_name": "",
    "logged_in": False,
    "username": "",
    "is_admin": False,
    "login_message": "",
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
}

.block-container {
    max-width: 1500px;
    padding-top: 1.2rem;
}

.hero {
    background: #131313;
    border: 1px solid #2b2b2b;
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 16px;
}

.hero-title {
    font-size: 32px;
    font-weight: 900;
}

.hero-sub {
    color: #999;
    margin-top: 7px;
}

.card {
    background: #131313;
    border: 1px solid #2b2b2b;
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 16px;
}

.workflow {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 10px;
    margin: 15px 0;
}

.step {
    background: #161616;
    border: 1px solid #303030;
    border-radius: 14px;
    padding: 14px 8px;
    text-align: center;
}

.step b {
    display: block;
    font-size: 20px;
    margin-bottom: 5px;
}

.step span {
    font-size: 12px;
    color: #aaa;
}

.badge {
    padding: 5px 10px;
    border-radius: 99px;
    border: 1px solid #444;
}

.small {
    color: #999;
    font-size: 13px;
}

.auth-box {
    max-width: 900px;
    margin: auto;
}

@media (max-width: 800px) {

    .workflow {
        grid-template-columns: repeat(2, 1fr);
    }

    .hero-title {
        font-size: 24px;
    }

}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# Secrets
# ============================================================

def get_secret(name):
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""

    if not value:
        value = os.getenv(name, "")

    return str(value or "").strip()


# ============================================================
# JSON 安全讀寫
# ============================================================

def load_json(path, default):
    path = Path(path)

    if not path.exists():
        return default

    try:
        text = path.read_text(encoding="utf-8").strip()

        if not text:
            return default

        return json.loads(text)

    except Exception:
        return default


def save_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = path.with_suffix(path.suffix + ".tmp")

    temp_path.write_text(
        json.dumps(
            obj,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    temp_path.replace(path)


# ============================================================
# 密碼系統
# ============================================================

def old_sha256(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def hash_password(password):
    """
    PBKDF2 密碼雜湊。
    格式：
    pbkdf2$迭代次數$salt$hash
    """

    iterations = 260000

    salt = py_secrets.token_hex(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )

    encoded = digest.hex()

    return f"pbkdf2${iterations}${salt}${encoded}"


def verify_password(password, stored_hash):
    if not stored_hash:
        return False

    # 新版 PBKDF2
    if stored_hash.startswith("pbkdf2$"):

        try:
            parts = stored_hash.split("$")

            if len(parts) != 4:
                return False

            iterations = int(parts[1])
            salt = parts[2]
            expected = parts[3]

            digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                iterations,
            )

            actual = digest.hex()

            return hmac.compare_digest(
                actual,
                expected,
            )

        except Exception:
            return False

    # 舊版 SHA256 相容
    return hmac.compare_digest(
        stored_hash,
        old_sha256(password),
    )


# ============================================================
# 帳號正規化
# ============================================================

def normalize_username(username):
    return (username or "").strip().lower()


def valid_username(username):
    return bool(
        re.fullmatch(
            r"[a-z0-9_.-]{3,30}",
            username or "",
        )
    )


# ============================================================
# 會員資料
# ============================================================

def get_members():
    data = load_json(MEMBERS_FILE, {})

    if not isinstance(data, dict):
        return {}

    return data


def ensure_admin():

    data = get_members()

    admin = data.get(ADMIN_USERNAME)

    if not isinstance(admin, dict):

        data[ADMIN_USERNAME] = {
            "password_hash": hash_password(
                ADMIN_PASSWORD
            ),
            "expires": None,
            "admin": True,
            "created": datetime.now().isoformat(
                timespec="seconds"
            ),
        }

        save_json(
            MEMBERS_FILE,
            data,
        )

        return

    changed = False

    if not admin.get("admin"):
        admin["admin"] = True
        changed = True

    if not admin.get("password_hash"):
        admin["password_hash"] = hash_password(
            ADMIN_PASSWORD
        )
        changed = True

    if changed:
        data[ADMIN_USERNAME] = admin
        save_json(
            MEMBERS_FILE,
            data,
        )


ensure_admin()


# ============================================================
# 會員期限
# ============================================================

def member_expired(member):

    if not member:
        return True

    expires = member.get("expires")

    # None / 空值 = 永久
    if not expires:
        return False

    try:
        expire_date = date.fromisoformat(
            str(expires)
        )

        return date.today() > expire_date

    except Exception:
        return False


# ============================================================
# 登入
# ============================================================

def login(username, password):

    username = normalize_username(username)

    if not username:
        return False, "請輸入帳號"

    if not password:
        return False, "請輸入密碼"

    data = get_members()

    member = data.get(username)

    if not isinstance(member, dict):
        return False, "帳號或密碼錯誤"

    stored_hash = member.get(
        "password_hash",
        "",
    )

    if not verify_password(
        password,
        stored_hash,
    ):
        return False, "帳號或密碼錯誤"

    if member_expired(member):
        return False, "會員已到期"

    # 舊版 SHA256 登入成功後自動升級密碼
    if not stored_hash.startswith("pbkdf2$"):

        member["password_hash"] = hash_password(
            password
        )

        data[username] = member

        save_json(
            MEMBERS_FILE,
            data,
        )

    st.session_state.logged_in = True
    st.session_state.username = username
    st.session_state.is_admin = bool(
        member.get("admin", False)
    )
    st.session_state.page = "Dashboard"

    return True, "登入成功"


# ============================================================
# 註冊
# ============================================================

def register(username, password):

    username = normalize_username(username)

    if not valid_username(username):
        return (
            False,
            "帳號需 3～30 字，只能使用英文、數字、_、.、-",
        )

    if len(password or "") < 6:
        return False, "密碼至少 6 碼"

    if len(password) > 128:
        return False, "密碼不可超過 128 碼"

    data = get_members()

    if username in data:
        return False, "帳號已存在，請直接登入"

    expires = (
        date.today()
        + timedelta(days=30)
    ).isoformat()

    data[username] = {
        "password_hash": hash_password(
            password
        ),
        "expires": expires,
        "admin": False,
        "created": datetime.now().isoformat(
            timespec="seconds"
        ),
    }

    save_json(
        MEMBERS_FILE,
        data,
    )

    # 立即重新讀取驗證，避免寫入失敗卻顯示成功
    verify_data = get_members()

    if username not in verify_data:
        return False, "會員資料寫入失敗，請重新註冊"

    return (
        True,
        "註冊完成，有效期 30 天，現在可以登入",
    )


# ============================================================
# 登出
# ============================================================

def logout():

    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.is_admin = False
    st.session_state.page = "Dashboard"

    st.session_state.analysis_result = ""
    st.session_state.shopee_result = ""
    st.session_state.jimeng_result = ""
    st.session_state.tiktok_result = ""
    st.session_state.current_product = {}
    st.session_state.image_bytes = None
    st.session_state.video_bytes = None
    st.session_state.video_name = ""


# ============================================================
# Gemini
# ============================================================

def create_gemini_client():

    if not HAS_GENAI:
        return None

    api_key = get_secret(
        "GEMINI_API_KEY"
    )

    if not api_key:
        return None

    try:
        return genai.Client(
            api_key=api_key
        )

    except Exception as exc:
        st.session_state.gemini_error = str(
            exc
        )
        return None


@st.cache_resource
def cached_gemini_client():

    return create_gemini_client()


def gemini_ready():

    return (
        HAS_GENAI
        and bool(
            get_secret(
                "GEMINI_API_KEY"
            )
        )
    )


def call_gemini(
    prompt,
    image=None,
    mime="image/jpeg",
):

    client = cached_gemini_client()

    if client is None:

        st.session_state.gemini_error = (
            "Gemini 無法連線。請確認 "
            "google-genai 已安裝，並設定 "
            "GEMINI_API_KEY。"
        )

        return None

    if image:

        encoded = base64.b64encode(
            image
        ).decode("utf-8")

        input_data = [
            {
                "type": "image",
                "mime_type": mime,
                "data": encoded,
            },
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

        except Exception as exc:

            last_error = str(exc)

    st.session_state.gemini_error = (
        last_error
        or "Gemini 沒有回傳內容"
    )

    return None


# ============================================================
# 商品分類
# ============================================================

def category(text):

    mapping = {
        "食品": [
            "芭樂",
            "水果",
            "零食",
            "食品",
            "茶",
            "咖啡",
            "糖",
        ],
        "保養美妝": [
            "洗面",
            "乳液",
            "精華",
            "面膜",
            "保養",
            "彩妝",
            "口紅",
        ],
        "3C": [
            "手機",
            "平板",
            "耳機",
            "充電",
            "鍵盤",
            "滑鼠",
            "電腦",
        ],
        "居家生活": [
            "收納",
            "清潔",
            "居家",
            "廚房",
            "杯",
            "鍋",
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

    text = (text or "").lower()

    for cat, words in mapping.items():

        if any(
            word.lower() in text
            for word in words
        ):
            return cat

    return "其他"


# ============================================================
# 商品核心規則
# ============================================================

RULES = """
商品圖片是商品外觀、品牌、Logo、包裝、顏色、
形狀、材質與圖片文字的最高優先來源。

只能使用圖片或使用者明確提供且不衝突的資料。

無法確認就寫「圖片無法確認」。

禁止虛構：
品牌、Logo、型號、規格、容量、重量、
尺寸、成分、功效、認證、產地、
圖片文字。

若資料與圖片衝突：
標示「⚠️ 商品資料與圖片可能不一致」。

影片必須保持原商品外觀。

不得改：
品牌、Logo、包裝、顏色、形狀、
材質、圖片文字。

不得憑空新增商品。
"""


# ============================================================
# AI Prompt
# ============================================================

def analysis_prompt(product):

    return f"""
你是「黑金剛 AI 蝦皮半自動化 2.5 PRO」
的商品視覺分析 AI。

商品名稱：
{product["name"]}

商品分類：
{product["category"]}

商品價格：
{product["price"]}

使用者賣點：
{product["selling"]}

{RULES}

請完整分析：

【商品分析】
【圖片辨識】
【商品類型】
【品牌】
【Logo】
【外觀】
【顏色】
【材質】
【包裝】
【圖片文字】
【可確認主要賣點】
【蝦皮 SEO 標題】
【蝦皮商品描述】
【短版銷售文案】
【TikTok Hook】
【TikTok 15 秒腳本】
【TikTok 30 秒腳本】
【即夢 AI 2.5 Prompt】
【商品影片分鏡】
【不確定資訊】
【圖片與資料衝突檢查】

影片規格：

9:16
1080x1920
高級商業商品廣告
電影級燈光
真實商品攝影
慢速推鏡
輕微環繞
淺景深
乾淨背景
商品主體清晰
"""


def shopee_prompt(product, analysis):

    return f"""
你是台灣蝦皮電商文案專家。

商品：
{product["name"]}

分類：
{product["category"]}

價格：
{product["price"]}

賣點：
{product["selling"]}

AI 商品分析：
{analysis}

{RULES}

請輸出：

【蝦皮 SEO 標題】
【商品描述】
【商品特色】
【主要賣點】
【使用情境】
【購買注意事項】
【短版銷售文案】
【TikTok Hook】
【TikTok 15 秒腳本】
【TikTok 30 秒腳本】
【搜尋關鍵字】

不得虛構商品資訊。
"""


def tiktok_prompt(product, analysis):

    return f"""
你是台灣 TikTok 電商短影音腳本專家。

商品：
{product["name"]}

商品分類：
{product["category"]}

商品分析：
{analysis}

{RULES}

請製作：

【Hook 1】
【Hook 2】
【Hook 3】

【15 秒完整腳本】

【30 秒完整腳本】

【字幕】
【口播】
【鏡頭】
【CTA】
【Hashtags】

影片比例：
9:16

解析度：
1080x1920
"""


def jimeng_prompt(product, analysis):

    return f"""
你是「黑金剛」
即夢 AI 2.5 商品影片 Prompt 專家。

商品：
{product["name"]}

商品分析：
{analysis}

{RULES}

建立一支 15 秒商品廣告。

格式：
9:16
1080x1920

時間軸：

0-3 秒：
建立乾淨高級商品場景。

3-6 秒：
慢速電影感推鏡。

6-9 秒：
輕微環繞商品。

9-12 秒：
商品細節特寫。

12-15 秒：
商品英雄鏡頭。

視覺：

高級商業廣告
電影級燈光
真實材質
自然反射
淺景深
乾淨背景
專業商品攝影

只輸出完整影片 Prompt。

不得修改商品本身。
不得新增 Logo。
不得新增不存在的文字。
不得改變品牌、包裝、顏色、
形狀與材質。
"""


# ============================================================
# 圖片處理
# ============================================================

def process_image(uploaded):

    raw = uploaded.getvalue()

    if len(raw) > MAX_IMAGE_MB * 1024 * 1024:
        raise ValueError(
            f"圖片不可超過 {MAX_IMAGE_MB} MB"
        )

    image = Image.open(
        io.BytesIO(raw)
    )

    image = ImageOps.exif_transpose(
        image
    )

    image.thumbnail(
        (
            MAX_IMAGE_SIZE,
            MAX_IMAGE_SIZE,
        )
    )

    if image.mode not in (
        "RGB",
        "L",
    ):
        image = image.convert("RGB")

    output = io.BytesIO()

    image.save(
        output,
        format="JPEG",
        quality=92,
    )

    return (
        output.getvalue(),
        "image/jpeg",
    )


# ============================================================
# 歷史紀錄
# ============================================================

def save_history(data):

    filename = (
        datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )
        + ".json"
    )

    save_json(
        HISTORY_DIR / filename,
        data,
    )


# ============================================================
# 登入畫面
# ============================================================

def login_page():

    st.markdown(
        f"""
        <div class="hero auth-box">
            <div class="hero-title">
                🥷 {APP_NAME}
            </div>

            <div class="hero-sub">
                商品分析 → 商品指令碼圖 →
                蝦皮 → TikTok → 即夢 →
                商品影片
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns(
        2
    )

    # --------------------------------------------------------
    # 登入
    # --------------------------------------------------------

    with left:

        st.subheader(
            "🔐 會員登入"
        )

        username = st.text_input(
            "帳號",
            key="login_username",
            placeholder="輸入你的帳號",
        )

        password = st.text_input(
            "密碼",
            type="password",
            key="login_password",
            placeholder="輸入你的密碼",
        )

        if st.button(
            "🚀 登入黑金剛",
            type="primary",
            use_container_width=True,
        ):

            ok, message = login(
                username,
                password,
            )

            # ★ 修正 DeltaGenerator
            if ok:

                st.success(
                    message
                )

                st.rerun()

            else:

                st.error(
                    message
                )

    # --------------------------------------------------------
    # 註冊
    # --------------------------------------------------------

    with right:

        st.subheader(
            "👤 註冊會員"
        )

        register_username = st.text_input(
            "新帳號",
            key="register_username",
            placeholder="3～30 字",
        )

        register_password = st.text_input(
            "新密碼",
            type="password",
            key="register_password",
            placeholder="至少 6 碼",
        )

        if st.button(
            "📝 註冊會員",
            use_container_width=True,
        ):

            ok, message = register(
                register_username,
                register_password,
            )

            if ok:

                # 註冊成功後，自動把帳號帶到登入框
                st.session
