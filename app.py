import json
import os
import hashlib
from datetime import datetime, date, timedelta
import streamlit as st

# 常數設定
APP_NAME = "黑金剛 AI"
APP_VERSION = "2.5"
MEMBERS_FILE = "members.json"
HISTORY_FILE = "history.json"

JIMENG_25_CORE_RULES = """
你是一位頂級 AI 視覺導演與即夢 AI 2.5 提示詞工程專家。
1. 畫面比例：9:16
2. 運鏡指令：Pan, Tilt, Zoom, Orbit
3. 視覺風格：電影級光影、超高畫質 8k
"""

# 輔助函式
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    return hash_password(password) == hashed_password

def load_members() -> dict:
    if os.path.exists(MEMBERS_FILE):
        try:
            with open(MEMBERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    default_admin = {
        "admin": {
            "username": "admin",
            "password": hash_password("admin123"),
            "role": "admin",
            "expires": "永久",
            "active": True,
            "created_at": datetime.now().isoformat(),
        }
    }
    save_members(default_admin)
    return default_admin

def save_members(members: dict):
    with open(MEMBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(members, f, ensure_ascii=False, indent=2)

def member_is_active(member: dict) -> bool:
    if not member.get("active", True):
        return False
    expires = member.get("expires")
    if expires == "永久":
        return True
    try:
        return date.today() <= date.fromisoformat(expires)
    except Exception:
        return False

def days_remaining(member: dict) -> int:
    expires = member.get("expires")
    if expires == "永久":
        return 9999
    try:
        return max(0, (date.fromisoformat(expires) - date.today()).days)
    except Exception:
        return 0

def load_history() -> list:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(record: dict):
    records = load_history()
    records.insert(0, record)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

def detect_product_category(name: str) -> str:
    food_keywords = ["甘草", "芭樂", "零食", "餅乾", "特產", "美食", "水果"]
    return "食品" if any(k in name for k in food_keywords) else "通用商品"

def process_image(uploaded_file):
    from PIL import Image
    import io
    image = Image.open(uploaded_file)
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return image, buf.getvalue()

# AI 生成模擬
def analyze_product(name, category, price, selling_points):
    return f"【分析報告】名稱：{name}｜分類：{category}｜價格：{price}｜賣點：{selling_points}"

def generate_shopee_copy(name, category, price, selling_points):
    return f"🔥【爆款推薦】{name}\n✨賣點：{selling_points}\n💰限時價：NT${price}\n#蝦皮好物 #{name}"

def generate_tiktok_copy(name, selling_points):
    return f"🎬 TikTok 15秒腳本：{name}\n[前3秒] 還在找{name}嗎？\n[賣點] {selling_points}\n[行動] 點擊左下角下單！"

def generate_seedance_prompt(name, category, price, selling_points):
    return f"{JIMENG_25_CORE_RULES}\nProduct: {name}\nStyle: 8k commercial photo --v 2.5"

# UI 初始化
def inject_css():
    st.markdown("<style>.hero{background:#1e1e1e;padding:1.5rem;border-radius:10px;color:white;text-align:center;}</style>", unsafe_allow_html=True)

def init_session():
    defaults = {
        "logged_in": False, "username": "", "role": "", "page": "Dashboard",
        "analysis_result": "", "generated_shopee": "", "generated_tiktok": "",
        "generated_jimeng": "", "gemini_error": ""
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# 頁面內容
def login_page():
    st.markdown(f"<div class='hero'><h1>⚫ {APP_NAME}</h1><p>AI 商品營運系統</p></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("登入系統")
        u = st.text_input("帳號", key="login_u")
        p = st.text_input("密碼", type="password", key="login_p")
        if st.button("登入", type="primary", use_container_width=True, key="login_btn"):
            members = load_members()
            m = members.get(u)
            if m and verify_password(p, m.get("password", "")):
                if not member_is_active(m):
                    st.error("帳號已停用或過期。")
                    return
                st.session_state.logged_in = True
                st.session_state.username = u
                st.session_state.role = m.get("role", "member")
                st.session_state.page = "Dashboard"
                st.rerun()
            else:
                st.error("帳號或密碼錯誤。")

def sidebar():
    members = load_members()
    current = members.get(st.session_state.username, {})
    with st.sidebar:
        st.title("⚫ 黑金剛")
        st.caption(f"使用者：{st.session_state.username}")
        st.divider()
        pages = ["Dashboard", "商品上架工作台", "歷史紀錄", "TikTok短影音", "蝦皮分潤管理"]
        if st.session_state.role == "admin":
            pages.append("管理員中心")
        selected = st.radio("選單", pages, key="menu_radio")
        st.session_state.page = selected
        st.divider()
        if st.button("登出", use_container_width=True, key="logout_btn"):
            st.session_state.logged_in = False
            st.rerun()

def dashboard():
    st.title("Dashboard")
    st.metric("歷史總紀錄數", len(load_history()))

def product_workspace():
    st.title("📦 商品上架工作台")
    c1, c2 = st.columns(2)
    with c1:
        p_name = st.text_input("商品名稱", key="p_name")
        p_cat = st.text_input("分類", key="p_cat")
        p_price = st.number_input("價格", value=999, key="p_price")
        p_points = st.text_area("賣點", key="p_points")
    with c2:
        uploaded = st.file_uploader("圖片", key="p_img")

    selected = st.multiselect("產生項目", ["商品分析", "蝦皮文案", "TikTok腳本", "即夢 Prompt"], default=["蝦皮文案", "即夢 Prompt"], key="p_select")
    if st.button("🚀 開始生成", type="primary", use_container_width=True, key="gen_btn"):
        if not p_name:
            st.warning("請輸入名稱")
            return
        cat = p_cat or detect_product_category(p_name)
        st.session_state.generated_shopee = generate_shopee_copy(p_name, cat, p_price, p_points) if "蝦皮文案" in selected else ""
        st.session_state.generated_jimeng = generate_seedance_prompt(p_name, cat, p_price, p_points) if "即夢 Prompt" in selected else ""
        save_history({
            "created_at": datetime.now().isoformat(),
            "username": st.session_state.username,
            "product": {"名稱": p_name, "價格": p_price},
            "shopee": st.session_state.generated_shopee,
            "jimeng": st.session_state.generated_jimeng
        })
        st.success("成功生成並儲存！")

    if st.session_state.generated_shopee:
        st.text_area("蝦皮文案", st.session_state.generated_shopee, height=200)
    if st.session_state.generated_jimeng:
        st.text_area("即夢 Prompt", st.session_state.generated_jimeng, height=300)

def history_page():
    st.title("🕘 歷史紀錄")
    records = load_history()
    for i, r in enumerate(records):
        with st.expander(f"{r.get('product', {}).get('名稱', '未知')} - {r.get('created_at', '')}"):
            st.json(r)

def tiktok_page():
    st.title("🎬 TikTok 短影音")
    name = st.text_input("商品名稱", key="tk_name")
    if st.button("產生腳本", key="tk_btn"):
        st.text_area("腳本結果", generate_tiktok_copy(name, "熱銷爆款"), height=300)

def affiliate_page():
    st.title("💰 蝦皮分潤試算")
    p = st.number_input("商品售價", value=1000, key="aff_p")
    c = st.number_input("分潤 %", value=5, key="aff_c")
    st.metric("預估收益", f"NT$ {p * c / 100:.0f}")

def admin_center():
    if st.session_state.role != "admin":
        return
    st.title("👑 管理員中心")
    members = load_members()
    st.write("目前會員清單：", list(members.keys()))
    
    u = st.text_input("新會員帳號", key="adm_u")
    p = st.text_input("新會員密碼", type="password", key="adm_p")
    if st.button("建立會員", key="adm_btn"):
        if u and p:
            members[u] = {
                "username": u,
                "password": hash_password(p),
                "role": "member",
                "expires": "永久",
                "active": True,
                "created_at": datetime.now().isoformat()
            }
            save_members(members)
            st.success("會員建立成功！")
            st.rerun()

def render_page():
    p = st.session_state.page
    if p == "Dashboard": dashboard()
    elif p == "商品上架工作台": product_workspace()
    elif p == "歷史紀錄": history_page()
    elif p == "TikTok短影音": tiktok_page()
    elif p == "蝦皮分潤管理": affiliate_page()
    elif p == "管理員中心": admin_center()

def main():
    st.set_page_config(page_title=APP_NAME, layout="wide")
    inject_css()
    init_session()
    if not st.session_state.logged_in:
        login_page()
    else:
        sidebar()
        render_page()

if __name__ == "__main__":
    main()
