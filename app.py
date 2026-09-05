# ============================================================
# 黑金剛 AI 蝦皮半自動化 2.5 PRO
# Streamlit Cloud 穩定版
# 單檔 app.py
# ============================================================

import base64
import hashlib
import io
import json
import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps


# ============================================================
# 基本設定
# ============================================================

APP_NAME = "黑金剛 AI 蝦皮半自動化 2.5 PRO"
APP_VERSION = "5.1-STABLE"

DATA_DIR = Path("data")
PRODUCT_DIR = DATA_DIR / "products"
HISTORY_DIR = DATA_DIR / "history"
MEDIA_DIR = DATA_DIR / "media"
MEMBERS_FILE = DATA_DIR / "members.json"

MAX_IMAGE_SIZE = 1600
MAX_IMAGE_MB = 20
MAX_VIDEO_MB = 300

DEFAULT_MEMBER_DAYS = 30

VIDEO_TYPES = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".webm": "video/webm",
}


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
        radial-gradient(circle at top right, rgba(255, 193, 7, 0.08), transparent 28%),
        radial-gradient(circle at bottom left, rgba(255, 255, 255, 0.04), transparent 25%),
        #090909;
    color: #f5f5f5;
}

.block-container {
    max-width: 1400px;
    padding-top: 1rem;
    padding-bottom: 3rem;
}

h1, h2, h3 {
    letter-spacing: 0.5px;
}

.hero {
    background: linear-gradient(135deg, #111111, #191919);
    border: 1px solid #2d2d2d;
    border-radius: 22px;
    padding: 28px;
    margin-bottom: 20px;
    box-shadow: 0 10px 35px rgba(0,0,0,0.35);
}

.hero-title {
    font-size: 32px;
    font-weight: 900;
    margin-bottom: 6px;
}

.hero-subtitle {
    color: #aaaaaa;
    font-size: 15px;
}

.card {
    background: #111111;
    border: 1px solid #292929;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 16px;
}

.gold {
    color: #f4c542;
}

.badge {
    display: inline-block;
    padding: 5px 11px;
    border-radius: 999px;
    background: #1d1d1d;
    border: 1px solid #3a3a3a;
    color: #f4c542;
    font-size: 12px;
    font-weight: 800;
}

.small {
    color: #999999;
    font-size: 13px;
}

.workflow {
    background: #111111;
    border: 1px solid #292929;
    border-radius: 16px;
    padding: 16px;
    margin: 7px 0;
}

.workflow b {
    color: #f4c542;
}

div[data-testid="stMetric"] {
    background: #111111;
    border: 1px solid #292929;
    border-radius: 16px;
    padding: 14px;
}

button[kind="primary"] {
    border-radius: 12px;
    font-weight: 800;
}

.stButton > button {
    border-radius: 12px;
    min-height: 42px;
}

textarea, input {
    border-radius: 10px !important;
}

[data-testid="stSidebar"] {
    background: #0d0d0d;
}

.login-box {
    max-width: 520px;
    margin: 30px auto;
    background: #111111;
    border: 1px solid #303030;
    border-radius: 24px;
    padding: 28px;
}

.footer {
    text-align: center;
    color: #666666;
    padding: 30px 0 10px;
    font-size: 12px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 建立資料夾
# ============================================================

for folder in [
    DATA_DIR,
    PRODUCT_DIR,
    HISTORY_DIR,
    MEDIA_DIR,
]:
    folder.mkdir(parents=True, exist_ok=True)


# ============================================================
# Session State
# ============================================================

DEFAULT_STATE = {
    "logged_in": False,
    "username": "",
    "is_admin": False,
    "page": "Dashboard",
    "gemini_model": "",
    "last_analysis": "",
    "last_shopee": "",
    "last_tiktok": "",
    "last_jimeng": "",
    "last_image_bytes": None,
    "last_image_name": "",
    "last_video_bytes": None,
    "last_video_name": "",
    "last_video_mime": "",
    "last_product_name": "",
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


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
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return True
    except Exception:
        return False


# ============================================================
# 會員系統
# ============================================================

def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def normalize_username(username):
    return username.strip().lower()


def valid_username(username):
    return bool(
        re.fullmatch(
            r"[a-z0-9_.-]{3,30}",
            username,
        )
    )


def ensure_default_admin():

    members = load_json(MEMBERS_FILE, [])

    if not isinstance(members, list):
        members = []

    found = False

    for member in members:
        if normalize_username(
            str(member.get("username", ""))
        ) == "admin":
            found = True
            break

    if not found:
        members.append(
            {
                "username": "admin",
                "password_hash": hash_password("admin123"),
                "created_at": datetime.now().isoformat(),
                "expires": None,
                "admin": True,
            }
        )

        save_json(MEMBERS_FILE, members)


ensure_default_admin()


def get_members():
    data = load_json(MEMBERS_FILE, [])

    if not isinstance(data, list):
        return []

    return data


def register_user(username, password, confirm):

    username = normalize_username(username)

    if not valid_username(username):
        return False, "帳號只能使用英文小寫、數字、底線、點或短橫線，長度 3～30。"

    if len(password) < 6:
        return False, "密碼至少需要 6 碼。"

    if password != confirm:
        return False, "兩次密碼不一致。"

    members = get_members()

    for member in members:
        if normalize_username(
            str(member.get("username", ""))
        ) == username:
            return False, "這個帳號已經存在。"

    expires = (
        date.today() + timedelta(days=DEFAULT_MEMBER_DAYS)
    ).isoformat()

    members.append(
        {
            "username": username,
            "password_hash": hash_password(password),
            "created_at": datetime.now().isoformat(),
            "expires": expires,
            "admin": False,
        }
    )

    if not save_json(MEMBERS_FILE, members):
        return False, "會員資料無法儲存。"

    return True, f"註冊成功，會員期限至 {expires}。"


def login_user(username, password):

    username = normalize_username(username)

    members = get_members()

    for member in members:

        if normalize_username(
            str(member.get("username", ""))
        ) != username:
            continue

        if member.get("password_hash") != hash_password(password):
            return False, "帳號或密碼錯誤。"

        expires = member.get("expires")

        if expires:
            try:
                expire_date = date.fromisoformat(str(expires))

                if expire_date < date.today():
                    return False, "會員期限已到期。"

            except Exception:
                return False, "會員期限資料格式錯誤。"

        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.is_admin = bool(
            member.get("admin", False)
        )

        return True, "登入成功。"

    return False, "帳號或密碼錯誤。"


def logout():

    for key, value in DEFAULT_STATE.items():
        st.session_state[key] = value

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
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]


def get_secret(name):

    try:
        value = st.secrets.get(name)

        if value:
            return str(value).strip()

    except Exception:
        pass

    value = os.getenv(name)

    if value:
        return value.strip()

    return ""


@st.cache_resource(show_spinner=False)
def get_gemini_client(api_key):

    if not HAS_GENAI:
        return None

    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def image_to_jpeg_bytes(uploaded_file):

    image = Image.open(uploaded_file)

    image = ImageOps.exif_transpose(image)

    if image.mode not in ["RGB", "L"]:
        background = Image.new(
            "RGB",
            image.size,
            "white",
        )

        if "A" in image.getbands():
            background.paste(
                image,
                mask=image.getchannel("A"),
            )
        else:
            background.paste(image)

        image = background

    else:
        image = image.convert("RGB")

    image.thumbnail(
        (MAX_IMAGE_SIZE, MAX_IMAGE_SIZE)
    )

    output = io.BytesIO()

    image.save(
        output,
        format="JPEG",
        quality=92,
        optimize=True,
    )

    return output.getvalue()


def build_ai_prompt(
    product_name,
    category,
    price,
    selling_points,
    target,
):

    return f"""
你是「黑金剛 AI 蝦皮半自動化 2.5 PRO」的電商 AI。

請分析使用者提供的商品圖片與資料。

【商品資料】
商品名稱：{product_name or "未提供"}
分類：{category or "未提供"}
價格：{price or "未提供"}
賣點：{selling_points or "未提供"}
平台：{target}

【最高優先規則】
商品圖片是視覺判斷的最高優先來源。

不可自行捏造：
- 品牌
- Logo
- 包裝
- 顏色
- 材質
- 型號
- 規格
- 容量
- 功能
- 成分
- 認證
- 數字
- 文字
- 使用效果
- 醫療功效
- 其他圖片無法確認的資訊

如果圖片無法確認，請寫：
「圖片無法確認」

如果文字資料與圖片看起來可能不一致，請標示：
「⚠️ 商品資料與圖片可能不一致」

請輸出繁體中文。

請依序輸出：

【一、商品分析】
1. 商品類型
2. 視覺特徵
3. 可確認賣點
4. 不可確認資訊
5. 電商定位

【二、蝦皮標題】
產生 3 個不同版本。

【三、蝦皮商品描述】
產生可以直接貼到蝦皮的完整描述。

【四、TikTok】
產生：
- 3 秒 Hook
- 15 秒腳本
- 畫面節奏
- CTA

【五、即夢 AI 2.5】
產生 9:16、15 秒商品影片 Prompt。

影片流程：
0-3 秒：商品建立
3-6 秒：慢速推近
6-9 秒：輕微環繞
9-12 秒：商品細節
12-15 秒：高級 Hero Shot

必須保持原商品：
品牌、Logo、包裝、形狀、顏色、材質、文字不可自行修改。

不要新增圖片中不存在的商品。
"""


def call_gemini(
    prompt,
    image_bytes=None,
):

    api_key = get_secret("GEMINI_API_KEY")

    if not api_key:
        return (
            False,
            "尚未設定 GEMINI_API_KEY。",
        )

    if not HAS_GENAI:
        return (
            False,
            "尚未安裝 google-genai。",
        )

    client = get_gemini_client(api_key)

    if client is None:
        return (
            False,
            "Gemini Client 建立失敗。",
        )

    contents = []

    if image_bytes:

        image_b64 = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        contents.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_b64,
                },
            }
        )

    contents.append(
        {
            "type": "text",
            "text": prompt,
        }
    )

    last_error = ""

    for model in GEMINI_MODELS:

        try:

            response = client.models.generate_content(
                model=model,
                contents=contents,
            )

            text = getattr(
                response,
                "text",
                None,
            )

            if text:
                st.session_state.gemini_model = model

                return True, text

            last_error = (
                f"{model} 沒有返回文字內容。"
            )

        except Exception as exc:

            last_error = (
                f"{model}: {type(exc).__name__}: {exc}"
            )

    return False, last_error


# ============================================================
# 登入頁
# ============================================================

def login_page():

    st.markdown(
        """
<div class="login-box">

<div class="hero-title">
🖤 黑金剛 AI
</div>

<div class="hero-subtitle">
蝦皮半自動化 2.5 PRO
</div>

<br>

<div class="badge">
PRO AI COMMERCE SYSTEM
</div>

</div>
""",
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs(
        ["🔐 登入", "📝 註冊"]
    )

    with tab_login:

        st.markdown("### 登入系統")

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
            type="primary",
            use_container_width=True,
        ):

            ok, msg = login_user(
                username,
                password,
            )

            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

        st.info(
            "第一次測試可以使用：帳號 admin / 密碼 admin123"
        )

    with tab_register:

        st.markdown("### 建立會員")

        username = st.text_input(
            "新帳號",
            key="register_username",
        )

        password = st.text_input(
            "新密碼",
            type="password",
            key="register_password",
        )

        confirm = st.text_input(
            "確認密碼",
            type="password",
            key="register_confirm",
        )

        if st.button(
            "建立會員",
            use_container_width=True,
        ):

            ok, msg = register_user(
                username,
                password,
                confirm,
            )

            if ok:
                st.success(msg)
            else:
                st.error(msg)


# ============================================================
# Dashboard
# ============================================================

def dashboard():

    st.markdown(
        """
<div class="hero">

<div class="hero-title">
🖤 黑金剛 AI 蝦皮半自動化 2.5 PRO
</div>

<div class="hero-subtitle">
商品圖片 → AI分析 → 蝦皮文案 → TikTok → 即夢影片 Prompt
</div>

<br>

<span class="badge">STABLE 5.1</span>

</div>
""",
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "登入會員",
            st.session_state.username,
        )

    with col2:
        st.metric(
            "AI 引擎",
            "Gemini",
        )

    with col3:
        st.metric(
            "短影音",
            "9:16",
        )

    with col4:
        st.metric(
            "商品影片",
            "15 秒",
        )

    st.markdown("### 🔥 工作流程")

    steps = [
        ("01", "商品圖片", "上傳商品圖片"),
        ("02", "AI 分析", "分析圖片與商品資訊"),
        ("03", "蝦皮文案", "產生標題與描述"),
        ("04", "TikTok", "產生短影音腳本"),
        ("05", "即夢 AI", "產生 9:16 影片 Prompt"),
    ]

    cols = st.columns(5)

    for col, item in zip(cols, steps):

        with col:

            st.markdown(
                f"""
<div class="workflow">

<div class="small">{item[0]}</div>

<b>{item[1]}</b>

<br>

<span class="small">
{item[2]}
</span>

</div>
""",
                unsafe_allow_html=True,
            )

    st.markdown("### ⚡ 快速開始")

    if st.button(
        "🚀 開始建立商品",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.page = "商品上架工作台"
        st.rerun()


# ============================================================
# 商品上架工作台
# ============================================================

def product_workspace():

    st.title("🛒 商品上架工作台")

    st.caption(
        "商品圖片是 AI 視覺分析的最高優先來源。"
    )

    with st.form("product_form"):

        product_name = st.text_input(
            "商品名稱",
            value=st.session_state.last_product_name,
        )

        category = st.selectbox(
            "商品分類",
            [
                "食品",
                "保養美妝",
                "3C",
                "居家生活",
                "服飾",
                "汽機車",
                "其他",
            ],
        )

        price = st.number_input(
            "商品價格",
            min_value=0,
            value=999,
            step=1,
        )

        selling_points = st.text_area(
            "商品賣點",
            placeholder="例如：方便攜帶、外觀設計、適合送禮……",
        )

        uploaded_image = st.file_uploader(
            "上傳商品圖片",
            type=["jpg", "jpeg", "png", "webp"],
        )

        submitted = st.form_submit_button(
            "🤖 開始 AI 商品分析",
            type="primary",
            use_container_width=True,
        )

    if uploaded_image:

        try:

            image_bytes = image_to_jpeg_bytes(
                uploaded_image
            )

            st.session_state.last_image_bytes = image_bytes
            st.session_state.last_image_name = uploaded_image.name
            st.session_state.last_product_name = product_name

            st.image(
                image_bytes,
                caption=uploaded_image.name,
                use_container_width=True,
            )

        except Exception as exc:
            st.error(
                f"圖片處理失敗：{type(exc).__name__}: {exc}"
            )
            return

    if submitted:

        if not product_name.strip():
            st.warning("請先輸入商品名稱。")
            return

        if not st.session_state.last_image_bytes:
            st.warning("請先上傳商品圖片。")
            return

        prompt = build_ai_prompt(
            product_name,
            category,
            price,
            selling_points,
            "蝦皮 + TikTok + 即夢 AI 2.5",
        )

        with st.spinner(
            "AI 正在分析商品，請稍候……"
        ):

            ok, result = call_gemini(
                prompt,
                st.session_state.last_image_bytes,
            )

        if ok:

            st.session_state.last_analysis = result

            st.success(
                f"分析完成｜模型：{st.session_state.gemini_model}"
            )

            st.markdown("### 🤖 AI 分析結果")

            st.markdown(result)

            save_product_record(
                product_name=product_name,
                category=category,
                price=price,
                selling_points=selling_points,
                ai_result=result,
            )

        else:

            st.error(result)

            st.info(
                "如果尚未設定 Gemini API，請到 Streamlit Cloud → Settings → Secrets 設定 GEMINI_API_KEY。"
            )


# ============================================================
# 商品指令碼圖
# ============================================================

def product_script():

    st.title("🎨 商品指令碼圖")

    st.markdown(
        """
<div class="card">

<b class="gold">商品視覺規則</b>

<p>
上傳商品圖片為最高優先來源。
</p>

<p class="small">
不可自行修改品牌、Logo、包裝、顏色、材質、
商品形狀、圖片文字與可辨識規格。
</p>

</div>
""",
        unsafe_allow_html=True,
    )

    if st.session_state.last_image_bytes:

        st.image(
            st.session_state.last_image_bytes,
            caption="目前商品圖片",
            use_container_width=True,
        )

        prompt = st.text_area(
            "補充需求",
            placeholder="例如：高級電商主視覺、蝦皮商品首圖……",
        )

        if st.button(
            "✨ 產生商品視覺 Prompt",
            type="primary",
            use_container_width=True,
        ):

            base = """
請根據目前商品圖片建立電商視覺 Prompt。

圖片中的商品必須保持原樣。

不可新增不存在的品牌、Logo、文字、包裝、
規格、配件、功能
