import streamlit as st
from PIL import Image, ImageOps
from pathlib import Path
from datetime import datetime, date, timedelta
import json
import hashlib
import secrets
import re

# ============================================================
# 黑金剛 AI 多 AI 總控中心 PRO
# VERSION: 3.0 NO API
# ============================================================

APP_NAME = "黑金剛 AI 多 AI 總控中心 PRO"
APP_VERSION = "3.0 NO-API"

DATA_DIR = Path("data")
MEDIA_DIR = DATA_DIR / "media"
HISTORY_DIR = DATA_DIR / "history"

MEMBERS_FILE = DATA_DIR / "members.json"
PRODUCTS_FILE = DATA_DIR / "products.json"
HISTORY_FILE = DATA_DIR / "history.json"

for folder in [DATA_DIR, MEDIA_DIR, HISTORY_DIR]:
    folder.mkdir(parents=True, exist_ok=True)


# ============================================================
# 基礎 JSON
# ============================================================

def load_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def safe_filename(text):
    text = re.sub(
        r"[^0-9A-Za-z\u4e00-\u9fff_-]+",
        "_",
        str(text)
    )
    return text[:80] or "file"


# ============================================================
# 初始化資料
# ============================================================

def init_data():

    members = load_json(MEMBERS_FILE, {})

    if not isinstance(members, dict):
        members = {}

    if "admin" not in members:
        members["admin"] = {
            "password": hash_password("admin123"),
            "role": "admin",
            "expires": "2099-12-31",
            "created": datetime.now().isoformat()
        }

    save_json(MEMBERS_FILE, members)

    if not PRODUCTS_FILE.exists():
        save_json(PRODUCTS_FILE, [])

    if not HISTORY_FILE.exists():
        save_json(HISTORY_FILE, [])


init_data()


# ============================================================
# Streamlit
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🖤",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CSS
# ============================================================

css = (
    "<style>"
    "html,body,[class*='css']{"
    "font-family:'Noto Sans TC',sans-serif;"
    "}"
    ".stApp{"
    "background:#0b0d10;"
    "color:#f5f5f5;"
    "}"
    "[data-testid='stSidebar']{"
    "background:#11151a;"
    "}"
    ".bk-hero{"
    "padding:24px;"
    "border:1px solid #303640;"
    "border-radius:20px;"
    "background:linear-gradient(135deg,#171b21,#0e1115);"
    "margin-bottom:20px;"
    "}"
    ".bk-hero h1{"
    "margin:0;"
    "font-size:30px;"
    "}"
    ".bk-hero p{"
    "color:#aeb6c1;"
    "margin:8px 0 0;"
    "}"
    ".bk-card{"
    "padding:18px;"
    "border:1px solid #2b3139;"
    "border-radius:16px;"
    "background:#12161b;"
    "margin-bottom:14px;"
    "}"
    ".bk-small{"
    "font-size:13px;"
    "color:#9da7b3;"
    "}"
    ".bk-big{"
    "font-size:25px;"
    "font-weight:700;"
    "}"
    ".bk-tag{"
    "display:inline-block;"
    "padding:5px 9px;"
    "margin:3px;"
    "border-radius:999px;"
    "background:#20262e;"
    "color:#dce1e7;"
    "font-size:12px;"
    "}"
    "</style>"
)

st.markdown(css, unsafe_allow_html=True)


# ============================================================
# 登入系統
# ============================================================

def is_expired(member):
    try:
        expire_date = date.fromisoformat(
            member.get("expires", "2000-01-01")
        )
        return date.today() > expire_date
    except Exception:
        return True


def login_user(username, password):

    members = load_json(MEMBERS_FILE, {})

    member = members.get(username)

    if not member:
        return False, "帳號或密碼錯誤"

    if member.get("password") != hash_password(password):
        return False, "帳號或密碼錯誤"

    if is_expired(member):
        return False, "會員已到期"

    st.session_state.user = username
    st.session_state.role = member.get("role", "member")

    return True, "登入成功"


# ============================================================
# 歷史紀錄
# ============================================================

def add_history(kind, title, content):

    rows = load_json(HISTORY_FILE, [])

    rows.insert(
        0,
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": st.session_state.get("user", ""),
            "kind": kind,
            "title": title,
            "content": content
        }
    )

    save_json(HISTORY_FILE, rows[:500])


# ============================================================
# 商品
# ============================================================

def save_product(data):

    products = load_json(PRODUCTS_FILE, [])

    product_id = secrets.token_hex(5)

    item = dict(data)
    item["id"] = product_id
    item["created"] = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    products.insert(0, item)

    save_json(PRODUCTS_FILE, products)

    return product_id


def detect_category(text):

    text = str(text).lower()

    category_map = {
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
            "糖"
        ],
        "美妝保養": [
            "洗面",
            "乳液",
            "精華",
            "面膜",
            "防曬",
            "洗髮",
            "保養",
            "香水",
            "洗髮"
        ],
        "3C": [
            "手機",
            "平板",
            "耳機",
            "充電",
            "鍵盤",
            "滑鼠",
            "電腦",
            "3c"
        ],
        "居家生活": [
            "清潔",
            "收納",
            "杯",
            "鍋",
            "家居",
            "居家",
            "用品"
        ],
        "服飾": [
            "衣",
            "褲",
            "鞋",
            "襪",
            "包",
            "帽",
            "服飾"
        ],
        "汽機車": [
            "汽車",
            "機車",
            "車用",
            "行車記錄器",
            "輪胎"
        ]
    }

    for category, keywords in category_map.items():

        for keyword in keywords:

            if keyword.lower() in text:
                return category

    return "其他"


# ============================================================
# 商品資料表單
# ============================================================

def product_form(key_prefix="main"):

    st.markdown(
        "<div class='bk-card'><b>📦 商品資料</b></div>",
        unsafe_allow_html=True
    )

    name = st.text_input(
        "商品名稱",
        placeholder="例如：甘草芭樂",
        key=key_prefix + "_name"
    )

    category = st.selectbox(
        "商品分類",
        [
            "自動判斷",
            "食品",
            "美妝保養",
            "3C",
            "居家生活",
            "服飾",
            "汽機車",
            "其他"
        ],
        key=key_prefix + "_category"
    )

    price = st.number_input(
        "商品價格",
        min_value=0,
        value=999,
        step=1,
        key=key_prefix + "_price"
    )

    points = st.text_area(
        "商品賣點",
        placeholder="一行一個賣點\n例如：天然風味\n方便攜帶\n日常零食",
        key=key_prefix + "_points"
    )

    image = st.file_uploader(
        "商品圖片",
        type=["png", "jpg", "jpeg", "webp"],
        key=key_prefix + "_image"
    )

    if category == "自動判斷":
        final_category = detect_category(name)
    else:
        final_category = category

    if image:
        try:
            st.image(
                image,
                caption="商品原始圖片",
                width=280
            )
        except Exception:
            pass

    return {
        "name": name.strip(),
        "category": final_category,
        "price": int(price),
        "points": points.strip()
    }


# ============================================================
# 蝦皮文案
# ============================================================

def generate_shopee_copy(data):

    name = data.get("name", "")
    category = data.get("category", "其他")
    price = data.get("price", 0)
    points = data.get("points", "")

    point_list = [
        x.strip()
        for x in points.splitlines()
        if x.strip()
    ]

    if not point_list:
        point_list = [
            "商品特色請依實際商品確認"
        ]

    joined = "、".join(point_list[:6])

    title1 = f"{name}｜{joined[:45]}"
    title2 = f"{name}｜{category} 熱門推薦｜日常實用"
    title3 = f"{name}｜精選商品｜優惠價 NT${price:,}"

    bullet_text = "\n".join(
        [f"• {x}" for x in point_list]
    )

    description = "\n".join(
        [
            f"【{name}】",
            "",
            f"商品分類：{category}",
            f"參考售價：NT$ {price:,}",
            "",
            "【商品特色】",
            bullet_text,
            "",
            "【購買提醒】",
            "• 商品尺寸、顏色、規格、成分請以實際商品為準。",
            "• 圖片無法確認的資料不自行虛構。",
            "• 出貨與售後規則請依實際賣場設定。"
        ]
    )

    return "\n".join(
        [
            "【蝦皮標題 1】",
            title1,
            "",
            "【蝦皮標題 2】",
            title2,
            "",
            "【蝦皮標題 3】",
            title3,
            "",
            "【商品描述】",
            description,
            "",
            "【搜尋關鍵字】",
            joined
        ]
    )


# ============================================================
# TikTok
# ============================================================

def generate_tiktok(data, seconds):

    name = data.get("name", "")
    category = data.get("category", "其他")
    points = [
        x.strip()
        for x in data.get("points", "").splitlines()
        if x.strip()
    ]

    p1 = points[0] if points else "商品特色"
    p2 = points[1] if len(points) > 1 else "日常使用方便"

    return "\n".join(
        [
            f"【TikTok {seconds} 秒商品短影音腳本】",
            f"商品：{name}",
            f"分類：{category}",
            "",
            "【0-3 秒｜Hook】",
            f"畫面：{name}快速出場，第一眼看清楚商品。",
            "字幕：先別滑走！",
            "旁白：這個商品你可能會需要。",
            "",
            "【3-7 秒｜第一賣點】",
            "畫面：商品細節特寫。",
            f"字幕：{p1}",
            "",
            "【7-11 秒｜第二賣點】",
            "畫面：切換另一個角度或實際使用情境。",
            f"字幕：{p2}",
            "",
            "【11-15 秒｜CTA】",
            "畫面：商品置中，乾淨背景。",
            "字幕：想了解更多，查看商品頁。",
            "",
            f"【延伸】若製作 {seconds} 秒版本，可增加商品細節、使用情境與 CTA。",
            "禁止自行增加未確認的品牌、規格、功效或成分。"
        ]
    )


# ============================================================
# 即夢圖片 Prompt
# ============================================================

def generate_jimeng_image(data, ratio):

    name = data.get("name", "")
    category = data.get("category", "其他")
    points = data.get("points", "")

    return "\n".join(
        [
            "【即夢 AI 商品圖片 Prompt】",
            "",
            f"商品名稱：{name}",
            f"商品分類：{category}",
            f"畫幅：{ratio}",
            "",
            "【最高優先規則】",
            "使用者上傳的商品圖片是唯一商品外觀來源。",
            "",
            "【商品一致性】",
            "保留原始品牌。",
            "保留原始 Logo。",
            "保留原始包裝。",
            "保留原始形狀。",
            "保留原始顏色。",
            "保留原始材質。",
            "保留原始標籤。",
            "保留圖片中可辨識的原始文字。",
            "",
            "不得自行創造不存在的品牌。",
            "不得自行創造不存在的 Logo。",
            "不得自行修改商品結構。",
            "不得自行修改商品顏色。",
            "不得增加不存在的配件。",
            "不得增加不存在的規格。",
            "不得虛構功效、成分或產品資訊。",
            "",
            "【視覺風格】",
            "高級商業攝影。",
            "乾淨背景。",
            "自然光影。",
            "商品主體清楚。",
            "真實材質。",
            "電商廣告質感。",
            "",
            f"【已知商品賣點】{points or '目前沒有提供，請不要自行補充。'}",
            "",
            "【負面要求】",
            "變形、錯誤 Logo、錯誤文字、假包裝、額外商品、錯誤顏色、錯誤規格、過度修圖。"
        ]
    )


# ============================================================
# 即夢影片指令碼
# ============================================================

def generate_jimeng_video(data, seconds):

    name = data.get("name", "")
    category = data.get("category", "其他")
    points = data.get("points", "")

    return "\n".join(
        [
            "【即夢 AI 商品影片完整指令碼】",
            "",
            f"商品：{name}",
            f"分類：{category}",
            f"影片比例：9:16",
            f"影片長度：約 {seconds} 秒",
            "",
            "【商品一致性最高優先】",
            "以上傳商品圖片作為唯一商品外觀來源。",
            "不要改變品牌。",
            "不要改變 Logo。",
            "不要改變包裝。",
            "不要改變商品形狀。",
            "不要改變商品顏色。",
            "不要改變材質。",
            "不要修改圖片中的商品文字。",
            "不要創造不存在的配件。",
            "不要創造不存在的規格。",
            "不要自行虛構功效或成分。",
            "",
            "【分鏡】",
            "0-3 秒：商品完整出場，乾淨背景。",
            "3-6 秒：鏡頭緩慢推近商品。",
            "6-9 秒：輕微環繞商品。",
            "9-12 秒：商品細節特寫。",
            "12-15 秒：商品英雄鏡頭，商品置中。",
            "",
            "【攝影】",
            "高級商業廣告攝影。",
            "穩定鏡頭。",
            "自然光影。",
            "真實材質。",
            "避免商品變形。",
            "",
            f"【商品賣點】{points or '未提供，禁止自行增加。'}",
            "",
            "【負面要求】",
            "錯誤 Logo、錯誤文字、錯誤包裝、商品變形、換色、增加配件、增加不存在商品、虛構資訊。"
        ]
    )


# ============================================================
# AI 指令碼
# ============================================================

def generate_ai_command(data, target, task):

    name = data.get("name", "")
    category = data.get("category", "其他")
    price = data.get("price", 0)
    points = data.get("points", "")

    return "\n".join(
        [
            f"【{target} 專用 AI 指令碼】",
            "",
            f"任務：{task}",
            f"商品：{name}",
            f"分類：{category}",
            f"價格：NT$ {price:,}",
            f"賣點：{points or '未提供'}",
            "",
            "【資料規則】",
            "以使用者提供的商品資料與圖片為最高優先來源。",
            "不要自行虛構品牌。",
            "不要自行虛構規格。",
            "不要自行虛構成分。",
            "不要自行虛構功效。",
            "不要自行修改商品外觀。",
            "",
            "如果資料不足，請直接寫：",
            "「無法確認，請人工確認」。",
            "",
            "請使用繁體中文。",
            "輸出要有清楚標題。",
            "輸出要可以直接使用。",
        ]
    )


# ============================================================
# AI 平台
# ============================================================

AI_PLATFORMS = {
    "🦞 AI 龍蝦 / Agent": {
        "description": "AI Agent、任務拆解、自動化工作流",
        "url": "https://openclaw.ai/"
    },
    "🐋 DeepSeek": {
        "description": "推理、程式、文案、資料整理",
        "url": "https://chat.deepseek.com/"
    },
    "🟢 Gemini": {
        "description": "圖片理解、研究、文案",
        "url": "https://gemini.google.com/"
    },
    "🤖 ChatGPT": {
        "description": "企劃、文案、工作流程",
        "url": "https://chatgpt.com/"
    },
    "🟣 Claude": {
        "description": "長文、分析、整理",
        "url": "https://claude.ai/"
    },
    "⚡ Grok": {
        "description": "社群、趨勢、創意",
        "url": "https://grok.com/"
    },
    "🌐 Perplexity": {
        "description": "網路搜尋、資料研究",
        "url": "https://www.perplexity.ai/"
    },
    "🟠 Qwen": {
        "description": "中文、多模態、推理",
        "url": "https://chat.qwen.ai/"
    },
    "🌙 Kimi": {
        "description": "長文件、研究、Agent",
        "url": "https://www.kimi.com/"
    },
    "🟦 Copilot": {
        "description": "搜尋、文案、圖片",
        "url": "https://copilot.microsoft.com/"
    }
}


# ============================================================
# 登入頁
# ============================================================

def show_login():

    st.markdown(
        "<div class='bk-hero'>"
        "<h1>🖤 黑金剛 AI 多 AI 總控中心 PRO</h1>"
        "<p>免 API｜多 AI｜蝦皮｜TikTok｜即夢｜圖片｜影片指令碼</p>"
        "</div>",
        unsafe_allow_html=True
    )

    login_tab, register_tab = st.tabs(
        ["🔐 登入", "📝 註冊"]
    )

    with login_tab:

        username = st.text_input(
            "帳號",
            key="login_username"
        )

        password = st.text_input(
            "密碼",
            type="password",
            key="login_password"
        )

        if st.button(
            "登入黑金剛",
            type="primary",
            use_container_width=True
        ):

            ok, message = login_user(
                username.strip(),
                password
            )

            if ok:
                st.rerun()
            else:
                st.error(message)

        st.caption(
            "測試管理員：admin / admin123"
        )

    with register_tab:

        new_username = st.text_input(
            "新帳號",
            key="register_username"
        )

        new_password = st.text_input(
            "新密碼",
            type="password",
            key="register_password"
        )

        if st.button(
            "建立會員",
            use_container_width=True
        ):

            members = load_json(
                MEMBERS_FILE,
                {}
            )

            username = new_username.strip()

            if not username:
                st.error("請輸入帳號。")

            elif len(new_password) < 4:
                st.error("密碼至少 4 碼。")

            elif username in members:
                st.error("帳號已存在。")

            else:

                members[username] = {
                    "password": hash_password(
                        new_password
                    ),
                    "role": "member",
                    "expires": (
                        date.today()
                        + timedelta(days=30)
                    ).isoformat(),
                    "created": datetime.now().isoformat()
                }

                save_json(
                    MEMBERS_FILE,
                    members
                )

                st.success(
                    "註冊完成，會員期限 30 天。"
                )


# ============================================================
# Sidebar
# ============================================================

def show_sidebar():

    with st.sidebar:

        st.markdown("## 🖤 黑金剛")
        st.caption(APP_VERSION)

        st.write(
            f"👤 {st.session_state.get('user', '')}"
        )

        menu = [
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
            "👑 管理中心"
        ]

        page = st.radio(
            "功能選單",
            menu,
            label_visibility="collapsed"
        )

        if st.button(
            "🚪 登出",
            use_container_width=True
        ):
            st.session_state.clear()
            st.rerun()

        return page


# ============================================================
# Dashboard
# ============================================================

def page_dashboard():

    st.markdown(
        "<div class='bk-hero'>"
        "<h1>🖤 黑金剛 AI 多 AI 總控中心 PRO</h1>"
        "<p>一個入口管理商品、AI 指令碼、圖片、影片與短影音。</p>"
        "</div>",
        unsafe_allow_html=True
    )

    products = load_json(
        PRODUCTS_FILE,
        []
    )

    history = load_json(
        HISTORY_FILE,
        []
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "商品",
        len(products)
    )

    c2.metric(
        "AI 任務",
        len(history)
    )

    c3.metric(
        "AI 平台",
        len(AI_PLATFORMS)
    )

    c4.metric(
        "API",
        "不需要"
    )

    st.markdown(
    
