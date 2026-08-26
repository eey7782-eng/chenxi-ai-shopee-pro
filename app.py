import streamlit as st
import sqlite3
import hashlib
import requests
import json

# -----------------------------------------------------------------------------
# 1. 資料庫初始化 (SQLite - 帳號資料永久保存)
# -----------------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def add_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users(username, password) VALUES (?,?)', (username, make_hashes(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username =? AND password = ?', (username, make_hashes(password)))
    data = c.fetchall()
    conn.close()
    return data

init_db()

# -----------------------------------------------------------------------------
# 2. 頁面設定與 Secrets 讀取
# -----------------------------------------------------------------------------
st.set_page_config(page_title="蝦皮多樣化 AI 帶貨影片生成器", layout="wide")

secrets_api_key = st.secrets.get("COZE_API_KEY", "")
secrets_bot_id = st.secrets.get("COZE_BOT_ID", "") or st.secrets.get("COZE_WORKFLOW_ID", "")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

# -----------------------------------------------------------------------------
# 3. 側邊欄：會員登入 / 註冊系統與 API 設定
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("👤 會員中心")
    
    if not st.session_state["logged_in"]:
        tab1, tab2 = st.tabs(["登入", "註冊帳號"])
        
        with tab1:
            login_user_input = st.text_input("帳號", key="login_user")
            login_pass_input = st.text_input("密碼", type="password", key="login_pass")
            if st.button("🔑 登入"):
                result = login_user(login_user_input, login_pass_input)
                if result:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = login_user_input
                    st.success(f"歡迎回來，{login_user_input}！")
                    st.rerun()
                else:
                    st.error("帳號或密碼錯誤！")
                    
        with tab2:
            reg_user_input = st.text_input("新帳號", key="reg_user")
            reg_pass_input = st.text_input("新密碼", type="password", key="reg_pass")
            if st.button("📝 註冊"):
                if reg_user_input and reg_pass_input:
                    if add_user(reg_user_input, reg_pass_input):
                        st.success("註冊成功！請切換到「登入」分頁進行登入。")
                    else:
                        st.warning("該帳號已經存在！")
                else:
                    st.warning("請填寫完整帳密！")
    else:
        st.write(f"當前登入會員：**{st.session_state['username']}**")
        if st.button("🚪 登出"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.rerun()
            
    st.divider()
    st.title("⚙️ API 參數設定")
    coze_api_key = st.text_input("Coze API Key:", value=secrets_api_key, type="password")
    bot_id = st.text_input("Bot ID:", value=secrets_bot_id)

# -----------------------------------------------------------------------------
# 4. 主頁面：蝦皮多樣化選擇與生成區
# -----------------------------------------------------------------------------
st.title("🎬 蝦皮多樣化 AI 帶貨影片生成器")

if not st.session_state["logged_in"]:
    st.info("👈 請先在左側欄進行 **登入** 或 **註冊帳號** 以開始使用系統。")
else:
    st.subheader(f"👋 歡迎，{st.session_state['username']}！請選擇你的商品與影片模板風格")
    
    # 步驟 1：輸入商品連結
    product_url = st.text_input("🔗 請輸入蝦皮商品連結：", placeholder="https://shopee.tw/product/...")

    st.markdown("---")
    st.markdown("### 🎨 選擇影片與文案模板")

    # 步驟 2：多樣化模板選擇選單
    col1, col2 = st.columns(2)
    
    with col1:
        category = st.selectbox(
            "🛍️ 商品品類模板：",
            ["美妝保養 💄", "服飾鞋包 👗", "3C 數碼 📱", "居家生活 🏠", "美食零食 🍕", "寵物用品 🐶", "通用熱銷 📦"]
        )
        
        style = st.selectbox(
            "🎬 影片視覺/文案風格：",
            ["🔥 爆款帶貨風 (強效推坑、限時優惠)", "📦 開箱實測風 (第一人稱、細節展示)", "✨ 質感極簡風 (高級感、美學氛圍)", "😂 搞笑梗片風 (吸引眼球、趣味情境)", "🔬 專業評測風 (成分解析、數據比較)"]
        )

    with col2:
        aspect_ratio = st.selectbox(
            "📐 影片比例 (適用的平台)：",
            ["9:16 (直式 - Reels / Shorts / TikTok / 蝦皮限時)", "1:1 (正方形 - 蝦皮主圖影片 / IG 貼文)", "16:9 (橫式 - YouTube / 官網Banner)"]
        )
        
        target_audience = st.selectbox(
            "🎯 目標受眾族群：",
            ["小資上班族 💼", "學生黨/小資族 🎓", "新手媽媽/家庭 👶", "精打細算/省錢族 💰", "潮流酷炫青年 ⚡"]
        )

    # 額外需求設定
    extra_prompt = st.text_area("✍️ 額外特殊要求 (可不填)：", placeholder="例如：強調現貨供應、滿499免運、或是加入折扣碼促銷訊息...")

    st.markdown("---")

    # 步驟 3：開始生成
    if st.button("🚀 立即自動生成多樣化影片與文案", type="primary", use_container_width=True):
        if not coze_api_key or not bot_id:
            st.error("❌ 請先在左側欄設定 Coze API Key 與 Bot ID！")
        elif not product_url:
            st.warning("⚠️ 請輸入蝦皮商品連結！")
        else:
            with st.spinner(f"⏳ 正在調用「{category} - {style}」模板生成中，約需 15-30 秒，請稍候..."):
                try:
                    headers = {
                        "Authorization": f"Bearer {coze_api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    # 針對 Bot 智能體的正確請求內容格式
                    prompt_text = f"請幫我分析蝦皮商品：{product_url}\n【模板參數】\n- 品類：{category}\n- 風格：{style}\n- 影片比例：{aspect_ratio}\n- 目標受眾：{target_audience}\n- 額外要求：{extra_prompt}"
                    
                    bot_payload = {
                        "bot_id": bot_id,
                        "user_id": st.session_state.get("username", "user123"),
                        "query": prompt_text,
                        "stream": False
                    }
                    
                    # 呼叫 Bot API
                    response = requests.post(
                        "https://api.coze.cn/open_api/v2/chat",
                        headers=headers,
                        json=bot_payload,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        res_json = response.json()
                        st.success("✅ 多樣化影片與文案生成成功！")
                        
                        # 解析 Bot 回傳訊息
                        messages = res_json.get("messages", [])
                        output_text = ""
                        for msg in messages:
                            if msg.get("type") == "answer":
                                output_text += msg.get("content", "") + "\n\n"
                        
                        if output_text:
                            st.markdown("### 📋 AI 生成結果")
                            st.markdown(output_text)
                        else:
                            st.json(res_json)
                    else:
                        st.error(f"❌ 生成失敗，錯誤碼：{response.status_code}")
                        st.write(response.text)
                except requests.exceptions.Timeout:
                    st.error("⏰ 請求超時，請檢查 Coze 側的模型是否設定為輕量高速模型（如 Doubao-pro 或 GPT-3.5）。")
                except Exception as e:
                    st.error(f"❌ 發生系統錯誤：{e}")
