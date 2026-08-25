import json
import os
import hashlib
import io
import pandas as pd
from datetime import datetime, date, timedelta
import streamlit as st

# 常數設定
APP_NAME = "黑金剛 AI"
APP_VERSION = "2.5 (蝦皮半自動版)"
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

# AI 生成模擬
def generate_shopee_title(name, category):
    return f"🔥【現貨速發】{name} ｜ 超值熱銷優選 #{category}"

def generate_shopee_copy(name, category, price, selling_points):
    return f"✨【{name}】必買三大理由：\n1. {selling_points or '嚴選品質，買得安心'}\n2. 高CP值，優惠價只要 NT$ {price}\n3. 快速出貨，售後有保障！\n\n📦 商品規格：\n- 類別：{category}\n- 狀態：全新現貨\n\n#蝦皮優選 #{category} #{name} #熱銷爆款"

def generate_seedance_prompt(name, category, price, selling_points):
    return f"{JIMENG_25_CORE_RULES}\nProduct: {name}\nStyle: 8k commercial photo --v 2.5"

# 蝦皮 CSV 批量檔案生成器
def export_shopee_csv(product_list):
    df_data = []
    for p in product_list:
        df_data.append({
            "商品名稱": p.get("title", ""),
            "商品描述": p.get("description", ""),
            "價格": p.get("price", 0),
            "庫存": p.get("stock", 99),
            "重量(kg)": p.get("weight", 0.5),
            "出貨天數": 2
        })
    df = pd.DataFrame(df_data)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
    return csv_buffer.getvalue()

# UI 初始化
def inject_css():
    st.markdown("<style>.hero{background:#1e1e1e;padding:1.5rem;border-radius:10px;color:white;text-align:center;}</style>", unsafe_allow_html=True)

def init_session():
    defaults = {
        "logged_in": False, "username": "", "role": "", "page": "Dashboard",
        "generated_title": "", "generated_shopee": "", "generated_jimeng": "",
        "shopee_queue": []
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# 登入與註冊頁面
def login_page():
    st.markdown(f"<div class='hero'><h1>⚫ {APP_NAME}</h1><p>蝦皮半自動化 AI 營運系統</p></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔑 會員登入", "📝 註冊帳號"])
        with tab1:
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
                    st.session_state.page = "蝦皮半自動工作台"
                    st.rerun()
                else:
                    st.error("帳號或密碼錯誤。")
                    
        with tab2:
            new_u = st.text_input("設定新帳號", key="reg_u")
            new_p = st.text_input("設定新密碼", type="password", key="reg_p")
            confirm_p = st.text_input("再次確認密碼", type="password", key="reg_cp")
            if st.button("免費註冊 (送 7 天試用)", use_container_width=True, key="reg_btn"):
                members = load_members()
                if not new_u or not new_p:
                    st.warning("請輸入帳號與密碼。")
                elif new_p != confirm_p:
                    st.error("兩次輸入的密碼不一致！")
                elif new_u in members:
                    st.error("此帳號已被註冊。")
                else:
                    # 調整為 7 天試用期
                    exp_date = (date.today() + timedelta(days=7)).isoformat()
                    members[new_u] = {
                        "username": new_u, "password": hash_password(new_p),
                        "role": "member", "expires": exp_date, "active": True,
                        "created_at": datetime.now().isoformat()
                    }
                    save_members(members)
                    st.success("註冊成功！已贈送 7 天免費試用，請切換至「會員登入」分頁進行登入。")

def sidebar():
    members = load_members()
    current = members.get(st.session_state.username, {})
    with st.sidebar:
        st.title("⚫ 黑金剛 AI")
        st.caption(f"使用者：{st.session_state.username}")
        
        # 顯示剩餘天數
        if current.get("expires") == "永久":
            st.success("♾️ 永久會員")
        else:
            st.info(f"⏳ 試用剩餘 {days_remaining(current)} 天")

        st.divider()
        pages = ["蝦皮半自動工作台", "批量匯出 CSV", "歷史紀錄"]
        if st.session_state.role == "admin":
            pages.append("管理員中心")
        selected = st.radio("選單", pages, key="menu_radio")
        st.session_state.page = selected
        st.divider()
        if st.button("登出", use_container_width=True, key="logout_btn"):
            st.session_state.logged_in = False
            st.rerun()

# 蝦皮半自動工作台
def shopee_auto_workspace():
    st.title("⚡ 蝦皮半自動上架工作台")
    
    c1, c2 = st.columns(2)
    with c1:
        p_name = st.text_input("商品名稱", key="p_name")
        p_cat = st.text_input("分類 (如：美食/服飾)", key="p_cat")
        p_price = st.number_input("蝦皮售價", value=299, key="p_price")
        p_stock = st.number_input("預設庫存", value=99, key="p_stock")
    with c2:
        p_points = st.text_area("核心賣點", placeholder="輸入產品優勢...", height=130, key="p_points")

    if st.button("🚀 生成蝦皮半自動文案", type="primary", use_container_width=True, key="gen_btn"):
        if not p_name:
            st.warning("請輸入商品名稱")
            return
        cat = p_cat or detect_product_category(p_name)
        st.session_state.generated_title = generate_shopee_title(p_name, cat)
        st.session_state.generated_shopee = generate_shopee_copy(p_name, cat, p_price, p_points)
        st.session_state.generated_jimeng = generate_seedance_prompt(p_name, cat, p_price, p_points)
        st.success("生成完成！")

    if st.session_state.generated_shopee:
        st.divider()
        st.subheader("1️⃣ 最佳化蝦皮標題")
        st.code(st.session_state.generated_title, language=None)

        st.subheader("2️⃣ 蝦皮內文描述")
        st.text_area("內文區塊", st.session_state.generated_shopee, height=200)

        if st.button("➕ 加入「蝦皮批量上架佇列」", use_container_width=True, key="add_queue_btn"):
            st.session_state.shopee_queue.append({
                "title": st.session_state.generated_title,
                "description": st.session_state.generated_shopee,
                "price": p_price,
                "stock": p_stock
            })
            st.success(f"已加入佇列！目前累積 {len(st.session_state.shopee_queue)} 件商品準備批量匯出。")

# 批量匯出 CSV 頁面
def export_page():
    st.title("📦 蝦皮批量匯出 (CSV)")
    queue = st.session_state.shopee_queue
    st.write(f"目前佇列中共有 **{len(queue)}** 筆待上架商品。")

    if queue:
        st.dataframe(pd.DataFrame(queue))
        csv_data = export_shopee_csv(queue)
        
        st.download_button(
            label="⬇️ 下載蝦皮批量上架 CSV 檔",
            data=csv_data,
            file_name=f"shopee_batch_{date.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True,
            key="dl_csv_btn"
        )
        if st.button("清空佇列", key="clear_queue"):
            st.session_state.shopee_queue = []
            st.rerun()
    else:
        st.info("請先到「蝦皮半自動工作台」生成商品並點擊「加入佇列」。")

def history_page():
    st.title("🕘 歷史紀錄")
    records = load_history()
    for r in records:
        with st.expander(f"{r.get('product', {}).get('名稱', '未知')} - {r.get('created_at', '')}"):
            st.json(r)

def admin_center():
    if st.session_state.role != "admin": return
    st.title("👑 管理員中心")
    members = load_members()
    st.write("目前帳號清單：", list(members.keys()))

def render_page():
    p = st.session_state.page
    if p == "蝦皮半自動工作台": shopee_auto_workspace()
    elif p == "批量匯出 CSV": export_page()
    elif p == "歷史紀錄": history_page()
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
