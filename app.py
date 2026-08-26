import streamlit as st
import requests
import json
import re

st.set_page_config(page_title="蝦皮分潤 AI 控制台", page_icon="🛍️", layout="wide")

# ==================== 1. 初始化帳號資料庫 ====================
if "user_db" not in st.session_state:
    st.session_state.user_db = {"admin": "123456"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

# ==================== 2. 登入/註冊 切換 ====================
if not st.session_state.logged_in:
    st.title("🔐 蝦皮分潤 AI 管理系統")
    tab1, tab2 = st.tabs(["🔑 會員登入", "📝 免費註冊帳號"])

    with tab1:
        with st.form("login_form"):
            login_user = st.text_input("帳號")
            login_pass = st.text_input("密碼", type="password")
            if st.form_submit_button("登入系統"):
                if login_user in st.session_state.user_db and st.session_state.user_db[login_user] == login_pass:
                    st.session_state.logged_in = True
                    st.session_state.current_user = login_user
                    st.rerun()
                else:
                    st.error("❌ 帳號或密碼錯誤！")

    with tab2:
        with st.form("register_form"):
            reg_user = st.text_input("設定帳號")
            reg_pass1 = st.text_input("設定密碼", type="password")
            reg_pass2 = st.text_input("確認密碼", type="password")
            if st.form_submit_button("完成註冊"):
                if not reg_user or not reg_pass1:
                    st.warning("⚠️ 帳號與密碼不可留空！")
                elif reg_user in st.session_state.user_db:
                    st.error("❌ 此帳號已被使用！")
                elif reg_pass1 != reg_pass2:
                    st.error("❌ 密碼不一致！")
                else:
                    st.session_state.user_db[reg_user] = reg_pass1
                    st.success("🎉 註冊成功！請切換至「會員登入」登入。")

    st.stop()

# ==================== 3. 側邊欄與管理功能 ====================
with st.sidebar:
    st.write(f"👤 當前會員：**{st.session_state.current_user}**")
    if st.button("🚪 登出"):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.rerun()

    st.markdown("---")
    
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

    st.header("⚙️ API 參數設定")
    default_key = st.secrets.get("COZE_API_KEY", "")
    coze_api_key = st.text_input("Coze API Key:", value=default_key, type="password")
    bot_id = st.text_input("Bot ID / Workflow ID:")

# ==================== 4. 主功能：影片與文案生成 ====================
st.title("🎬 蝦皮自動化 AI 帶貨影片生成器")

shopee_url = st.text_input("請貼上蝦皮商品網址：", placeholder="https://shopee.tw/product/...")
custom_prompt = st.text_area("補充要求（可不填）：", placeholder="例如：主打高 CP 值、搞笑風格...")

if st.button("🚀 立即自動生成影片與文案", type="primary"):
    if not shopee_url:
        st.warning("請先輸入蝦皮商品網址！")
    elif not coze_api_key or not bot_id:
        st.error("請在左側欄填寫 Coze API Key 與 Bot ID！")
    else:
        with st.spinner("🎬 正在使用即夢 AI 自動繪製並渲染帶貨影片中，請稍候..."):
            full_prompt = f"""
            任務：請根據蝦皮商品網址生成 1 段帶貨影片與推廣文案。
            商品網址: {shopee_url}
            額外要求: {custom_prompt}
            
            請務必：
            1. 調用即夢/doubao 影片生成工具，將生成的 MP4 影片網址直接輸出。
            2. 附帶一段吸引人的社群推廣文案。
            """
            
            url = "https://api.coze.cn/open_api/v2/chat"
            headers = {
                "Authorization": f"Bearer {coze_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "conversation_id": f"video_job_{st.session_state.current_user}",
                "bot_id": bot_id,
                "user": st.session_state.current_user,
                "query": full_prompt,
                "stream": False
            }

            try:
                res = requests.post(url, headers=headers, json=payload, timeout=120)
                if res.status_code == 200:
                    data = res.json()
                    reply = ""
                    if "messages" in data:
                        for msg in data["messages"]:
                            if msg.get("type") == "answer":
                                reply += msg.get("content", "")
                    
                    st.success("🎉 影片與文案生成成功！")
                    
                    # 抓取回應中的 MP4 / 網址並顯示播放器
                    video_urls = re.findall(r'https?://[^\s<>"]+\.(?:mp4|mov)', reply)
                    
                    if video_urls:
                        st.markdown("### 🎥 自動生成帶貨影片")
                        for v_url in video_urls:
                            st.video(v_url)
                    
                    st.markdown("### 📝 推廣文案")
                    st.markdown(reply)
                else:
                    st.error(f"請求失敗: {res.text}")
            except Exception as e:
                st.error(f"連線錯誤: {e}")
