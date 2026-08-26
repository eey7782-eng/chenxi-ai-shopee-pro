import streamlit as st
import requests
import json

st.set_page_config(page_title="蝦皮分潤 AI 控制台", page_icon="🛍️", layout="wide")

# ==================== 1. 初始化帳號資料庫 (Session 內建) ====================
if "user_db" not in st.session_state:
    # 預設管理員：admin / 123456
    st.session_state.user_db = {
        "admin": "123456"
    }

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

# ==================== 2. 未登入狀態（開放註冊 / 登入 切換） ====================
if not st.session_state.logged_in:
    st.title("🔐 蝦皮分潤 AI 管理系統")
    
    tab1, tab2 = st.tabs(["🔑 會員登入", "📝 免費註冊帳號"])

    # --- 頁籤 1：登入 ---
    with tab1:
        with st.form("login_form"):
            login_user = st.text_input("帳號")
            login_pass = st.text_input("密碼", type="password")
            submit_login = st.form_submit_button("登入系統")

            if submit_login:
                if login_user in st.session_state.user_db and st.session_state.user_db[login_user] == login_pass:
                    st.session_state.logged_in = True
                    st.session_state.current_user = login_user
                    st.success("登入成功！正在載入...")
                    st.rerun()
                else:
                    st.error("❌ 帳號或密碼錯誤，或該帳號尚未註冊！")

    # --- 頁籤 2：使用者自行註冊 ---
    with tab2:
        st.subheader("建立新會員帳號")
        with st.form("register_form"):
            reg_user = st.text_input("設定帳號")
            reg_pass1 = st.text_input("設定密碼", type="password")
            reg_pass2 = st.text_input("確認密碼", type="password")
            submit_reg = st.form_submit_button("完成註冊")

            if submit_reg:
                if not reg_user or not reg_pass1:
                    st.warning("⚠️ 帳號與密碼不可留空！")
                elif reg_user in st.session_state.user_db:
                    st.error("❌ 此帳號已被使用，請換一個名稱！")
                elif reg_pass1 != reg_pass2:
                    st.error("❌ 兩次密碼輸入不一致！")
                else:
                    st.session_state.user_db[reg_user] = reg_pass1
                    st.success("🎉 註冊成功！請切換至「會員登入」頁籤登入。")

    st.stop()

# ==================== 3. 登入後專區 & 管理員功能 ====================
with st.sidebar:
    st.write(f"👤 當前會員：**{st.session_state.current_user}**")
    if st.button("🚪 登出"):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.rerun()

    st.markdown("---")
    
    # 👑 管理員專用：刪除會員帳號
    if st.session_state.current_user == "admin":
        st.header("👑 管理員後台")
        with st.expander("❌ 刪除指定會員帳號"):
            other_users = [u for u in st.session_state.user_db.keys() if u != "admin"]
            if other_users:
                del_user = st.selectbox("選擇要刪除的帳號：", other_users)
                if st.button("確認刪除", type="primary"):
                    del st.session_state.user_db[del_user]
                    st.success(f"已刪除帳號：{del_user}")
                    st.rerun()
            else:
                st.info("目前沒有其他會員可刪除。")
        st.markdown("---")

    # API 設定
    st.header("⚙️ API 參數設定")
    default_key = st.secrets.get("COZE_API_KEY", "")
    coze_api_key = st.text_input("Coze API Key:", value=default_key, type="password")
    bot_id = st.text_input("Bot ID / Workflow ID:")

# ==================== 4. 主功能頁面 ====================
st.title("🛍️ 蝦皮自動化文案與影音控制台")

shopee_url = st.text_input("請貼上蝦皮商品網址：", placeholder="https://shopee.tw/product/...")
custom_prompt = st.text_area("補充要求（可不填）：", placeholder="例如：主打高 CP 值、搞笑風格...")

if st.button("🚀 開始自動生成文案與影片腳本", type="primary"):
    if not shopee_url:
        st.warning("請先輸入蝦皮商品網址！")
    elif not coze_api_key or not bot_id:
        st.error("請在側邊欄填寫 Coze API Key 與 Bot ID！")
    else:
        with st.spinner("🤖 Gemini & Coze 正在分析商品並生成推廣內容..."):
            full_prompt = f"""
            請幫我針對以下蝦皮商品生成爆款帶貨內容：
            商品連結: {shopee_url}
            額外要求: {custom_prompt}
            
            請輸出：
            1. 吸引人的社群文案（含 Hashtag）
            2. 15 秒短影音腳本（包含畫面描述與旁白）
            3. 建議推廣的商品賣點
            """
            
            url = "https://api.coze.cn/open_api/v2/chat"
            headers = {
                "Authorization": f"Bearer {coze_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "conversation_id": f"job_{st.session_state.current_user}",
                "bot_id": bot_id,
                "user": st.session_state.current_user,
                "query": full_prompt,
                "stream": False
            }

            try:
                res = requests.post(url, headers=headers, json=payload, timeout=60)
                if res.status_code == 200:
                    data = res.json()
                    reply = ""
                    if "messages" in data:
                        for msg in data["messages"]:
                            if msg.get("type") == "answer":
                                reply += msg.get("content", "")
                    
                    st.success("🎉 生成完成！")
                    st.markdown("### 📝 生成結果")
                    st.markdown(reply)
                else:
                    st.error(f"請求失敗: {res.text}")
            except Exception as e:
                st.error(f"連線錯誤: {e}")
