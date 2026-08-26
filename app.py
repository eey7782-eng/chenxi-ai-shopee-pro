import streamlit as st
import requests
import json

st.set_page_config(page_title="蝦皮分潤 AI 控制台", page_icon="🛍️", layout="wide")

# ==================== 1. 初始化會員資料庫 (Session 內建) ====================
if "user_db" not in st.session_state:
    # 預設管理員帳號：admin / 密碼：123456
    st.session_state.user_db = {
        "admin": "123456"
    }

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

# ==================== 2. 登入介面 (未開放公開註冊) ====================
if not st.session_state.logged_in:
    st.title("🔐 蝦皮分潤 AI 管理系統")
    st.caption("提示：不提供自由註冊，如需帳號請聯繫管理員。")
    
    with st.form("login_form"):
        user_input = st.text_input("帳號")
        pass_input = st.text_input("密碼", type="password")
        submit_button = st.form_submit_button("登入系統")

        if submit_button:
            if user_input in st.session_state.user_db and st.session_state.user_db[user_input] == pass_input:
                st.session_state.logged_in = True
                st.session_state.current_user = user_input
                st.success("登入成功！正在載入...")
                st.rerun()
            else:
                st.error("❌ 帳號或密碼錯誤！")
    st.stop()

# ==================== 3. 登入後的 VIP 專區 & 會員管理 ====================
with st.sidebar:
    st.write(f"👤 當前使用者：**{st.session_state.current_user}**")
    if st.button("🚪 登出"):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.rerun()

    st.markdown("---")
    
    # 👑 管理員專用：會員新增與刪除區塊
    if st.session_state.current_user == "admin":
        st.header("👑 會員帳號管理")
        
        # --- 新增會員 ---
        with st.expander("➕ 新增會員帳號"):
            new_u = st.text_input("新帳號", key="add_u")
            new_p = st.text_input("新密碼", type="password", key="add_p")
            if st.button("確認新增"):
                if new_u and new_p:
                    st.session_state.user_db[new_u] = new_p
                    st.success(f"已成功新增帳號：{new_u}")
                else:
                    st.warning("請填寫完整的帳號與密碼！")

        # --- 刪除會員 ---
        with st.expander("❌ 刪除會員帳號"):
            # 列出除了 admin 以外的會員
            other_users = [u for u in st.session_state.user_db.keys() if u != "admin"]
            if other_users:
                del_user = st.selectbox("選擇要刪除的帳號：", other_users)
                if st.button("確認刪除", type="primary"):
                    del st.session_state.user_db[del_user]
                    st.success(f"已成功刪除帳號：{del_user}")
                    st.rerun()
            else:
                st.info("目前無可刪除的其他會員帳號。")

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
