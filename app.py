import streamlit as st
import sqlite3
import hashlib

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
# 2. 頁面設定
# -----------------------------------------------------------------------------
st.set_page_config(page_title="蝦皮爆款短影音 AI 指令生成器", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

# -----------------------------------------------------------------------------
# 3. 側邊欄：會員登入 / 註冊系統
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("👤 會員授權中心")
    
    if not st.session_state["logged_in"]:
        tab1, tab2 = st.tabs(["登入", "註冊帳號"])
        
        with tab1:
            login_user_input = st.text_input("帳號", key="login_user")
            login_pass_input = st.text_input("密碼", type="password", key="login_pass")
            if st.button("🔑 登入系統"):
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
            if st.button("📝 註冊授權"):
                if reg_user_input and reg_pass_input:
                    if add_user(reg_user_input, reg_pass_input):
                        st.success("註冊成功！請切換到「登入」分頁進行登入。")
                    else:
                        st.warning("該帳號已經存在！")
                else:
                    st.warning("請填寫完整帳密！")
    else:
        st.write(f"當前授權使用者：**{st.session_state['username']}**")
        if st.button("🚪 登出系統"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.rerun()

# -----------------------------------------------------------------------------
# 4. 主頁面：Prompt 生成與跳轉
# -----------------------------------------------------------------------------
st.title("🎬 蝦皮爆款短影音 AI 指令生成器")

if not st.session_state["logged_in"]:
    st.info("👈 請先在左側欄進行 **登入** 或 **輸入授權碼註冊** 以開始使用系統。")
else:
    st.subheader(f"👋 歡迎，{st.session_state['username']}！請設定你的商品與腳本需求")
    
    product_url = st.text_input("🔗 請輸入蝦皮商品連結 / 品名：", placeholder="例如：https://shopee.tw/product/... 或 韓系顯瘦寬褲")

    st.markdown("---")
    st.markdown("### 🎨 選擇帶貨模板參數")

    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("🛍️ 商品品類：", ["美妝保養 💄", "服飾鞋包 👗", "3C 數碼 📱", "居家生活 🏠", "美食零食 🍕", "寵物用品 🐶", "通用熱銷 📦"])
        style = st.selectbox("🎬 影片風格：", ["🔥 爆款帶貨風 (強效推坑、限時優惠)", "📦 開箱實測風 (第一人稱、細節展示)", "✨ 質感極簡風 (高級感、美學氛圍)", "😂 搞笑梗片風 (吸引眼球、趣味情境)", "🔬 專業評測風 (成分解析、數據比較)"])

    with col2:
        aspect_ratio = st.selectbox("📐 影片格式：", ["9:16 (直式 - Reels / Shorts / TikTok / 蝦皮限時)", "1:1 (正方形 - 蝦皮主圖影片 / IG 貼文)", "16:9 (橫式 - YouTube)"])
        target_audience = st.selectbox("🎯 目標受眾：", ["小資上班族 💼", "學生黨/小資族 🎓", "新手媽媽/家庭 👶", "精打細算/省錢族 💰", "潮流酷炫青年 ⚡"])

    extra_prompt = st.text_area("✍️ 額外特殊要求 (可不填)：", placeholder="例如：強調現貨供應、滿499免運、或是加入折扣碼促銷訊息...")

    st.markdown("---")

    if st.button("⚡ 1秒合成爆款 AI 指令 (Prompt)", type="primary", use_container_width=True):
        if not product_url:
            st.warning("⚠️ 請輸入蝦皮商品連結或品名！")
        else:
            # 合成精密的 Prompt
            generated_prompt = f"""你是一位專業的蝦皮短影音爆款帶貨導演兼資深文案師。
請根據以下參數，為這件蝦皮商品撰寫一份可以直接拿去拍攝與發布的「分鏡腳本 + 社群帶貨文案 + 搜尋標籤」。

【商品與模板資訊】
- 商品連結/品名：{product_url}
- 商品品類：{category}
- 視覺與文案風格：{style}
- 影片比例：{aspect_ratio}
- 目標受眾：{target_audience}
- 額外要求：{extra_prompt if extra_prompt else '無'}

【輸出格式要求】
1. 💡 影片主題與核心賣點（前 3 秒 Hook 吸睛重點）
2. 🎬 秒數分鏡腳本表（包含：分鏡秒數、視覺畫面、口播旁白/字幕、背景音效/BGM）
3. ✍️ 社群爆款帶貨文案（包含強效 Call-to-Action 促銷導流用語）
4. 🏷️ 10 個高搜尋量標籤 (Hashtags)"""

            st.success("✅ 爆款指令已成功生成！")
            st.markdown("### 📋 請複製下方指令，並貼入免費 AI 工具使用：")
            st.code(generated_prompt, language="markdown")

            st.markdown("---")
            st.markdown("### 🚀 免費 AI 工具捷徑 (點擊直接開啟網頁貼上)：")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.link_button("👉 前往 Google Gemini (免費)", "https://gemini.google.com/", use_container_width=True)
            with c2:
                st.link_button("👉 前往 ChatGPT (免費)", "https://chatgpt.com/", use_container_width=True)
            with c3:
                st.link_button("👉 前往 Claude (免費)", "https://claude.ai/", use_container_width=True)
