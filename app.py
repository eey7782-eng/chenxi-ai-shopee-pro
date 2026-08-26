import streamlit as st
import requests
import json
import re

st.set_page_config(page_title="蝦皮分潤 AI 自動化工具", page_icon="🛍️", layout="wide")

# ==================== 1. 登入系統 ====================
USER_CREDENTIALS = {"admin": "123456"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 蝦皮分潤 AI 控制台登入")
    with st.form("login_form"):
        user = st.text_input("帳號")
        password = st.text_input("密碼", type="password")
        if st.form_submit_button("登入"):
            if user in USER_CREDENTIALS and USER_CREDENTIALS[user] == password:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("帳號或密碼錯誤")
    st.stop()

# ==================== 2. 主介面 ====================
st.title("🛍️ 蝦皮分潤 AI 自動文案與影片生成器")

with st.sidebar:
    st.header("⚙️ API 設定")
    default_key = st.secrets.get("COZE_API_KEY", "")
    coze_api_key = st.text_input("Coze API Key:", value=default_key, type="password")
    bot_id = st.text_input("Bot / Workflow ID:")
    st.markdown("---")
    affiliate_id = st.text_input("你的蝦皮分潤追蹤碼 (SubID/ID):", help="用於紀錄分潤追蹤")

# 頁籤分類
tab1, tab2 = st.tabs(["🔗 單品自動生成", "📋 爆款商品分類指南"])

with tab1:
    shopee_url = st.text_input("請貼上蝦皮商品網址：", placeholder="https://shopee.tw/product/...")
    custom_prompt = st.text_area("補充要求（可不填）：", placeholder="例如：主打 CP 值高、客群為小資女、風格要搞笑狂熱...")

    if st.button("🚀 開始自動生成文案與影片腳本", type="primary"):
        if not shopee_url:
            st.warning("請先輸入蝦皮商品網址！")
        elif not coze_api_key or not bot_id:
            st.error("請在側邊欄填寫 Coze API Key 與 Bot ID！")
        else:
            with st.spinner("🤖 Gemini & Coze 正在分析商品並生成推廣內容..."):
                # 組合帶給 Coze 的 Prompt
                full_prompt = f"""
                請幫我針對以下蝦皮商品生成爆款帶貨內容：
                商品連結: {shopee_url}
                額外要求: {custom_prompt}
                
                請輸出：
                1. 吸引人的社群文案（含 Hashtag）
                2. 15 秒短影音腳本（包含畫面描述與旁白）
                3. 建議推廣的商品亮點賣點
                """
                
                # 發送請求至 Coze
                url = "https://api.coze.cn/open_api/v2/chat"
                headers = {
                    "Authorization": f"Bearer {coze_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "conversation_id": "shopee_affiliate_job",
                    "bot_id": bot_id,
                    "user": "affiliate_user",
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

with tab2:
    st.markdown("""
    ### 🎯 蝦皮分潤最容易爆單的 6 大品類與切入點
    
    * **美妝個護**：主打「前後對比」、「平價替代（平替）」、「成分黨解析」。
    * **居家收納**：主打「痛點解決」、「視覺前後整理差別」、「小空間神器」。
    * **3C 週邊**：主打「實測耐用度」、「外觀顏值」、「CP 值對比」。
    * **時尚穿搭**：主打「一衣多穿」、「顯瘦穿搭」、「學生/小資質感」。
    * **吃貨美食**：主打「開箱試吃」、「辦公室零食」、「團購限時優惠」。
    * **寵物母嬰**：主打「養寵必備」、「新手爸媽不踩雷」、「高黏著度消耗品」。
    """)
