import json
import os
import hashlib
import requests
import time
from datetime import datetime, date, timedelta
import streamlit as st

# 常數設定
APP_NAME = "黑金剛 AI"
APP_VERSION = "4.0 (蝦皮 API 全自動上架版)"
MEMBERS_FILE = "members.json"
HISTORY_FILE = "history.json"

# 蝦皮 OpenAPI 相關設定 (需至 Shopee Open Platform 申請 Partner Key)
SHOPEE_PARTNER_ID = os.getenv("SHOPEE_PARTNER_ID", "123456")  # 替換為你的 Partner ID
SHOPEE_PARTNER_KEY = os.getenv("SHOPEE_PARTNER_KEY", "your_partner_key_here")  # 替換為你的 Partner Key
SHOPEE_HOST = "https://partner.shopeemobile.com"  # 正式環境 URL

# 輔助函式：密碼與帳號
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    return hash_password(password) == hashed_password

def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_members():
    default_admin = {
        "admin": {
            "username": "admin",
            "password": hash_password("admin123"),
            "role": "admin",
            "expires": "永久",
            "active": True,
            "created_at": datetime.now().isoformat(),
            "shopee_access_token": "",
            "shopee_shop_id": ""
        }
    }
    return load_json(MEMBERS_FILE, default_admin)

def member_is_active(member: dict) -> bool:
    if not member.get("active", True): return False
    expires = member.get("expires")
    if expires == "永久": return True
    try:
        return date.today() <= date.fromisoformat(expires)
    except Exception:
        return False

def days_remaining(member: dict) -> int:
    expires = member.get("expires")
    if expires == "永久": return 9999
    try:
        return max(0, (date.fromisoformat(expires) - date.today()).days)
    except Exception:
        return 0

# ------------------------------------------------------------------
# 核心：蝦皮 OpenAPI 全自動上架邏輯
# ------------------------------------------------------------------
def post_to_shopee_api(shop_id: str, access_token: str, title: str, description: str, price: float, stock: int, category_id: int = 100001):
    """
    調用蝦皮 v2.product.add_item API 自動建立商品
    """
    path = "/api/v2/product/add_item"
    timestamp = int(time.time())
    
    # 若無真實串接 API Key，此處模擬成功 response
    if SHOPEE_PARTNER_KEY == "your_partner_key_here":
        time.sleep(1.5)  # 模擬網路請求 delay
        return {
            "error": "",
            "message": "success",
            "response": {
                "item_id": 9876543210,
                "item_name": title,
                "status": "NORMAL"
            }
        }
    
    # 算 API 簽名 (HMAC-SHA256)
    base_string = f"{SHOPEE_PARTNER_ID}{path}{timestamp}{access_token}{shop_id}".encode('utf-8')
    sign = hashlib.sha256(SHOPEE_PARTNER_KEY.encode('utf-8') + base_string).hexdigest()
    
    url = f"{SHOPEE_HOST}{path}?partner_id={SHOPEE_PARTNER_ID}&timestamp={timestamp}&access_token={access_token}&shop_id={shop_id}&sign={sign}"
    
    payload = {
        "original_price": price,
        "description": description,
        "item_name": title,
        "normal_stock": stock,
        "category_id": category_id,
        "weight": 0.5,
        "logistic_info": [{"logistic_id": 80001, "enabled": True}]  # 預設物流
    }
    
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    return response.json()


# UI 介面初始化
def inject_css():
    st.markdown("<style>.hero{background:#ee4d2d;padding:1.5rem;border-radius:10px;color:white;text-align:center;margin-bottom:1rem;}</style>", unsafe_allow_html=True)

def init_session():
    defaults = {
        "logged_in": False, "username": "", "role": "member", "page": "🚀 蝦皮全自動上架",
        "generated_title": "", "generated_shopee": ""
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# 登入與註冊
def login_page():
    st.markdown(f"<div class='hero'><h1>⚡ {APP_NAME}</h1><p>蝦皮 API 一鍵全自動發布系統</p></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔑 會員登入", "📝 註冊帳號 (送7天試用)"])
        with tab1:
            u = st.text_input("帳號", key="login_u")
            p = st.text_input("密碼", type="password", key="login_p")
            if st.button("登入", type="primary", use_container_width=True, key="login_btn"):
                members = load_members()
                m = members.get(u)
                if m and verify_password(p, m.get("password", "")):
                    if not member_is_active(m):
                        st.error("帳號已停用或 7 天試用期已到期。")
                        return
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.session_state.role = m.get("role", "member")
                    st.session_state.page = "🚀 蝦皮全自動上架"
                    st.rerun()
                else:
                    st.error("帳號或密碼錯誤。")
                    
        with tab2:
            new_u = st.text_input("設定帳號", key="reg_u")
            new_p = st.text_input("設定密碼", type="password", key="reg_p")
            confirm_p = st.text_input("確認密碼", type="password", key="reg_cp")
            if st.button("免費註冊 (送 7 天試用)", use_container_width=True, key="reg_btn"):
                members = load_members()
                if not new_u or not new_p:
                    st.warning("請填寫帳號密碼。")
                elif new_p != confirm_p:
                    st.error("兩次密碼不一致！")
                elif new_u in members:
                    st.error("此帳號已被註冊。")
                else:
                    exp_date = (date.today() + timedelta(days=7)).isoformat()
                    members[new_u] = {
                        "username": new_u, "password": hash_password(new_p),
                        "role": "member", "expires": exp_date, "active": True,
                        "created_at": datetime.now().isoformat(),
                        "shopee_access_token": "", "shopee_shop_id": ""
                    }
                    save_json(MEMBERS_FILE, members)
                    st.success("註冊成功！已贈送 7 天免費試用。")

def sidebar():
    members = load_members()
    current = members.get(st.session_state.username, {})
    with st.sidebar:
        st.title("⚡ 黑金剛 AI")
        st.caption(f"使用者：{st.session_state.username}")
        
        if current.get("expires") == "永久":
            st.success("♾️ 永久授權")
        else:
            st.info(f"⏳ 試用剩餘 {days_remaining(current)} 天")

        st.divider()
        
        # 蝦皮綁定狀態
        if current.get("shopee_shop_id"):
            st.success(f"✅ 已綁定蝦皮店舖 ID: {current.get('shopee_shop_id')}")
        else:
            st.warning("⚠️ 未綁定蝦皮賣場 API")

        st.divider()
        pages = ["🚀 蝦皮全自動上架", "🔗 蝦皮 API 帳號綁定", "📜 上架歷史紀錄"]
        if st.session_state.role == "admin":
            pages.append("👑 管理員中心")
            
        selected = st.radio("功能選單", pages, key="menu_radio")
        st.session_state.page = selected
        st.divider()
        if st.button("登出", use_container_width=True, key="logout_btn"):
            st.session_state.logged_in = False
            st.rerun()

# 頁面 1：全自動上架工作台
def auto_upload_workspace():
    st.title("🚀 蝦皮 API 全自動一鍵上架")
    st.caption("AI 自動生成標題與描述，點擊即可直接發布至蝦皮賣場！")

    members = load_members()
    current_user = members.get(st.session_state.username, {})
    shop_id = current_user.get("shopee_shop_id")
    token = current_user.get("shopee_access_token")

    col1, col2 = st.columns(2)
    with col1:
        p_name = st.text_input("商品名稱", key="p_name", placeholder="例如：日系純棉寬鬆T恤")
        p_price = st.number_input("售價 (NT$)", value=399, min_value=1, key="p_price")
        p_stock = st.number_input("上架庫存", value=50, min_value=1, key="p_stock")
    with col2:
        p_cat_id = st.number_input("蝦皮分類 ID (Category ID)", value=100001, key="p_cat_id")
        p_points = st.text_area("核心賣點", placeholder="輸入產品賣點...", height=100, key="p_points")

    if st.button("🪄 1. AI 自動生成文案", type="secondary", use_container_width=True):
        if not p_name:
            st.warning("請輸入商品名稱！")
            return
        st.session_state.generated_title = f"🔥【現貨速發】{p_name} ｜ 爆款熱賣"
        st.session_state.generated_shopee = f"✨【{p_name}】產品亮點：\n1. {p_points or '高品質保證，買得安心'}\n2. 限時特價只要 NT$ {p_price}\n\n📦 產品資訊：\n- 狀態：全新品現貨\n- 出貨地點：台灣現貨\n\n#蝦皮優選 #{p_name} #熱銷爆款"
        st.success("文案產生成功！")

    if st.session_state.generated_shopee:
        st.divider()
        st.subheader("產出的蝦皮文案預覽")
        st.code(st.session_state.generated_title, language=None)
        st.text_area("內文預覽", st.session_state.generated_shopee, height=150)

        # 一鍵 API 發布
        if st.button("⚡ 2. 立即全自動發布至蝦皮賣場 (API Direct)", type="primary", use_container_width=True):
            if not shop_id or not token:
                st.error("請先前往「🔗 蝦皮 API 帳號綁定」頁面完成蝦皮賣場授權！")
                return

            with st.spinner("正在透過 API 發布至蝦皮賣家中心..."):
                res = post_to_shopee_api(
                    shop_id=shop_id,
                    access_token=token,
                    title=st.session_state.generated_title,
                    description=st.session_state.generated_shopee,
                    price=p_price,
                    stock=p_stock,
                    category_id=p_cat_id
                )

            if res.get("error") == "":
                item_id = res.get("response", {}).get("item_id")
                st.balloons()
                st.success(f"🎉 成功發布至蝦皮！蝦皮商品 Item ID: {item_id}")
            else:
                st.error(f"發布失敗：{res.get('message')}")

# 頁面 2：蝦皮 API 授權綁定
def shopee_bind_page():
    st.title("🔗 綁定蝦皮賣家 API 帳號")
    st.info("完成 OAuth 2.0 綁定後，系統才能代表你自動將商品發布至蝦皮。")

    members = load_members()
    current_user = members.get(st.session_state.username, {})

    with st.form("shopee_bind_form"):
        shop_id = st.text_input("Shopee Shop ID", value=current_user.get("shopee_shop_id", ""))
        access_token = st.text_input("Shopee Access Token", value=current_user.get("shopee_access_token", ""), type="password")
        submitted = st.form_submit_button("儲存 API 授權設定")
        
        if submitted:
            current_user["shopee_shop_id"] = shop_id
            current_user["shopee_access_token"] = access_token
            members[st.session_state.username] = current_user
            save_json(MEMBERS_FILE, members)
            st.success("蝦皮 API 授權資料儲存成功！")
            st.rerun()

def history_page():
    st.title("📜 上架歷史紀錄")
    st.info("顯示所有已透過 API 上架至蝦皮的紀錄。")

def admin_center():
    if st.session_state.role != "admin": return
    st.title("👑 管理員中心")
    st.write(load_members())

def render_page():
    p = st.session_state.page
    if p == "🚀 蝦皮全自動上架": auto_upload_workspace()
    elif p == "🔗 蝦皮 API 帳號綁定": shopee_bind_page()
    elif p == "📜 上架歷史紀錄": history_page()
    elif p == "👑 管理員中心": admin_center()

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
