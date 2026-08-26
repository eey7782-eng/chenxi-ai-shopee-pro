import streamlit as st
import requests
import json
import streamlit_authenticator as stauth

# 1. 頁面基本配置
st.set_page_config(page_title="Coze AI 會員控制台", page_icon="🔐", layout="wide")

# 2. 設定會員帳號密碼 (可自行修改或新增會員)
# 格式：'帳號': {'name': '顯示姓名', 'password': '密碼'}
credentials = {
    'usernames': {
        'admin': {
            'name': 'VIP 會員 A',
            'password': '123'  # 請修改為你的密碼
        },
        'user2': {
            'name': 'VIP 會員 B',
            'password': '456'  # 第二組會員密碼
        }
    }
}

# 3. 初始化登入模組
authenticator = stauth.Authenticate(
    credentials,
    'coze_cookie_name',
    'coze_signature_key',
    cookie_expiry_days=30
)

# 4. 渲染登入介面
authenticator.login()

# 5. 判斷登入狀態
if st.session_state["authentication_status"] is False:
    st.error("❌ 帳號或密碼錯誤！")
elif st.session_state["authentication_status"] is None:
    st.warning("🔒 請先輸入帳號密碼登入系統。")
elif st.session_state["authentication_status"]:
    # ==================== 以下為登入成功後的 VIP 區域 ====================
    
    # 側邊欄：登出按鈕與 API 設定
    with st.sidebar:
        st.write(f"歡迎回來，**{st.session_state['name']}**！")
        authenticator.logout('登出系統', 'main')
        st.markdown("---")
        st.header("⚙️ Coze 參數設定")
        coze_api_key = st.text_input("輸入 Coze API Key (pat_...):", type="password")
        bot_id = st.text_input("輸入 Bot ID 或 Workflow ID:")

    st.title("🤖 Coze AI 專屬會員工作台")

    # 初始化對話歷史紀錄
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 渲染過往對話
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 對話輸入處理
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
                "conversation_id": f"user_{st.session_state['username']}",
                "bot_id": bot_id,
                "user": st.session_state['username'],
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
