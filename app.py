import streamlit as st

# 1. 頁面基本設定
st.set_page_config(page_title="AI 帶貨影片生成器", layout="wide")

# 2. 自動讀取 Secrets（若沒有則給預設空字串，避免程式 Crash）
secrets_api_key = st.secrets.get("COZE_API_KEY", "")
secrets_bot_id = st.secrets.get("COZE_BOT_ID", "") or st.secrets.get("COZE_WORKFLOW_ID", "")

# 3. 側邊欄 API 設定
with st.sidebar:
    st.title("⚙️ API 參數設定")
    
    # 登入狀態提示
    if "user" not in st.session_state:
        st.session_state["user"] = "saleprice65"
    st.write(f"👤 當前會員：**{st.session_state['user']}**")
    
    # 輸入框：優先使用 Secrets 的預設值
    coze_api_key = st.text_input("Coze API Key:", value=secrets_api_key, type="password")
    bot_id = st.text_input("Bot ID / Workflow ID:", value=secrets_bot_id)

# 4. 主頁面內容（不設定嚴格的 if 擋住，確保永遠能顯示 UI）
st.title("🎬 AI 帶貨影片生成器")
st.subheader("自動生成蝦皮商品影片與行銷文案")

# 商品網址輸入框
product_url = st.text_input("請輸入蝦皮商品連結：", placeholder="https://shopee.tw/product/...")

# 執行按鈕
if st.button("🚀 立即自動生成影片與文案", type="primary"):
    # 點擊按鈕時才檢查 API Key 與 Bot ID
    if not coze_api_key or not bot_id:
        st.error("❌ 請先在左側欄填入 Coze API Key 與 Bot ID！")
    elif not product_url:
        st.warning("⚠️ 請輸入商品連結！")
    else:
        st.info("⏳ 正在調用 Coze API 生成中，請稍候...")
        # 這裡放置你原本調用 Coze API 的邏輯
        st.success("✅ 生成成功！（此處接你的 API 回傳結果）")
