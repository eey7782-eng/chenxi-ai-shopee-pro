import streamlit as st
import requests
import json

# 頁面配置
st.set_page_config(page_title="Coze AI 會員系統", page_icon="🔐", layout="wide")

# ==================== 1. 初始化資料庫 (Session 模擬) ====================
if "user_db" not in st.session_state:
    # 預設一組管理員帳密：帳號 admin / 密碼 123456
    st.session_state.user_db = {"admin": "123456"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# ==================== 2. 未登入狀態（登入/註冊 切換） ====================
if not st.session_state.logged_in:
    
    # 使用 Tab 頁籤切換「登入」與「註冊」
    tab1, tab2 = st.tabs(["🔑 會員登入", "📝 免費註冊"])

    # --- 頁籤 1：登入 ---
    with tab1:
        st.subheader("歡迎回來，請登入")
        with st.form("login_form"):
            login_user = st.text_input("帳號")
            login_pass = st.text_input("密碼", type="password")
            submit_login = st.form_submit_button("立即登入")

            if submit_login:
                if login_user in st.session_state.user_db and st.session_state.user_db[login_user] == login_pass:
                    st.session_state.logged_in = True
                    st.session_state.username = login_user
                    st.success("登入成功！正在載入...")
                    st.rerun()
                else:
                    st.error("❌ 帳號或密碼錯誤，或該帳號尚未註冊！")

    # --- 頁籤 2：註冊 ---
    with tab2:
        st.subheader("建立新帳號")
        with st.form("register_form"):
            reg_user = st.text_input("設定新帳號 (英文/數字)")
            reg_pass1 = st.text_input("設定密碼", type="password")
            reg_pass2 = st.text_input("再次確認密碼", type="password")
            submit_reg = st.form_submit_button("完成註冊")

            if submit_reg:
                if not reg_user or not reg_pass1:
                    st.warning("⚠️ 帳號與密碼不能留空！")
                elif reg_user in st.session_state.user_db:
                    st.error("❌ 此帳號已被註冊，請換一個帳號名稱！")
                elif reg_pass1 != reg_pass2:
                    st.error("❌ 兩次輸入的密碼不一致！")
                else:
                    # 將新帳號寫入資料庫
                    st.session_state.user_db[reg_user] = reg_pass1
                    st.success("🎉 註冊成功！請切換至「會員登入」頁籤進行登入。")

# ==================== 3. 登入後的 VIP 專區 ====================
else:
    with st.sidebar:
        st.write(f"👤 會員：**{st.session_state.username}**")
        if st.button("🚪 登出"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
            
        st.markdown("---")
        st.header("⚙️ Coze 參數設定")
        
        default_key = st.secrets.get("COZE_API_KEY", "")
        coze_api_key = st.text_input("Coze API Key:", value=default_key, type="password")
        bot_id = st.text_input("Bot ID / Workflow ID:")

    st.title("🤖 Coze AI 專屬會員工作台")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("請輸入提示詞 (Prompt)..."):
        if not coze_api_key or not bot_id:
            st.error("❌ 請先在左側欄填寫 API Key 與 Bot ID！")
            st.stop()

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("⏳ AI 處理中...")

            url = "https://api.coze.cn/open_api/v2/chat"
            headers = {
                "Authorization": f"Bearer {coze_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "conversation_id": f"user_{st.session_state.username}",
                "bot_id": bot_id,
                "user": st.session_state.username,
                "query": prompt,
                "stream": False
            }

            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    reply_text = ""
                    if "messages" in data:
                        for msg in data["messages"]:
                            if msg.get("type") == "answer":
                                reply_text += msg.get("content", "")
                    
                    if not reply_text:
                        reply_text = "已接收回應：\n```json\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n```"

                    message_placeholder.markdown(reply_text)
                    st.session_state.messages.append({"role": "assistant", "content": reply_text})
                else:
                    st.error(f"❌ 請求失敗 [HTTP {response.status_code}]: {response.text}")
            except Exception as e:
                st.error(f"⚠️ 連線錯誤：{e}")
