import os
import subprocess
import sys

# 自動檢查並安裝 edge-tts
try:
    import edge_tts
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "edge-tts"])
    import edge_tts

import streamlit as st
import sqlite3
import hashlib
import asyncio

# --- 1. 資料庫初始化 (SQLite) ---
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

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

def add_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users(username, password) VALUES (?,?)', (username, make_hashes(password)))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def login_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username =? AND password = ?', (username, make_hashes(password)))
    data = c.fetchall()
    conn.close()
    return data

async def generate_speech(text, output_file):
    # 使用免費微軟語音引擎 (台灣女聲：曉臻)
    communicate = edge_tts.Communicate(text, "zh-TW-HsiaoChenNeural")
    await communicate.save(output_file)

# --- 2. 頁面配置與初始化 ---
st.set_page_config(page_title="蝦皮爆款 AI 短影音系統", page_icon="🎬", layout="wide")
init_db()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""

# --- 3. 側邊欄：登入/註冊與功能導覽 ---
st.sidebar.title("👤 會員中心")

if not st.session_state['logged_in']:
    auth_mode = st.sidebar.radio("請選擇操作", ["登入", "註冊帳號"])
    
    if auth_mode == "登入":
        user = st.sidebar.text_input("帳號")
        passwd = st.sidebar.text_input("密碼", type="password")
        if st.sidebar.button("登入系統"):
            result = login_user(user, passwd)
            if result:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user
                st.sidebar.success(f"歡迎回來，{user}！")
                st.rerun()
            else:
                st.sidebar.error("帳號或密碼錯誤")

    elif auth_mode == "註冊帳號":
        new_user = st.sidebar.text_input("新帳號")
        new_passwd = st.sidebar.text_input("新密碼", type="password")
        if st.sidebar.button("免費註冊"):
            if new_user and new_passwd:
                if add_user(new_user, new_passwd):
                    st.sidebar.success("註冊成功！請切換至登入頁面")
                else:
                    st.sidebar.error("該帳號已被註冊")
            else:
                st.sidebar.warning("請填寫完整資訊")

else:
    st.sidebar.write(f"當前登入者：**{st.session_state['username']}**")
    if st.sidebar.button("登出系統"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        st.rerun()
        
    st.sidebar.markdown("---")
    menu_choice = st.sidebar.selectbox("🎯 選擇工具模式", ["🎬 爆款 AI 指令生成器", "🔊 AI 語音合成器"])

    # --- 功能一：爆款 AI 指令生成器 ---
    if menu_choice == "🎬 爆款 AI 指令生成器":
        st.title("🎬 蝦皮爆款短影音 AI 指令生成器")
        st.write("👋 請輸入商品資訊，系統將自動為你生成專屬提示詞！")
        
        prod_link = st.text_input("🔗 請輸入蝦皮商品連結 / 品名：", placeholder="例如：https://shopee.tw/... 或 韓系顯瘦寬褲")
        category = st.selectbox("🛍️ 商品品類：", ["服飾鞋包 👗", "美妝保養 💄", "居家生活 🏠", "3C 數碼 📱", "美食零食 🍿"])
        style = st.selectbox("🎬 影片風格：", ["🔥 爆款帶貨風 (強效推坑、限時優惠)", "✨ 高質感開箱風", "💡 痛點解決風"])
        ratio = st.selectbox("📐 影片格式：", ["9:16 (直式 - Reels / Shorts / TikTok / 蝦皮限時)", "16:9 (橫式)"])
        target = st.selectbox("🎯 目標受眾：", ["小資上班族 💼", "學生黨 🎓", "全職媽媽 👩‍👧‍👦", "追求高 CP 值小資族"])
        extra = st.text_input("✍️ 額外特殊要求 (可不填)：", placeholder="例如：強調現貨供應、滿499免運...")

        if st.button("🚀 點擊生成專屬提示詞"):
            if prod_link:
                prompt_result = f"""你是一位專業的蝦皮短影音爆款帶貨導演兼資深文案師。
請根據以下參數，為這件蝦皮商品撰寫一份可以直接拿去拍攝與發布的「分鏡腳本 + 社群帶貨文案 + 搜尋標籤」。

【商品與模板資訊】
- 商品連結/品名：{prod_link}
- 商品品類：{category}
- 視覺與文案風格：{style}
- 影片比例：{ratio}
- 目標受眾：{target}
- 額外要求：{extra if extra else '無'}

【輸出格式要求】
1. 💡 影片主題與核心賣點（前 3 秒 Hook 吸睛重點）
2. 🎬 秒數分鏡腳本表（包含：分鏡秒數、視覺畫面、口播旁白/字幕、背景音效/BGM）
3. ✍️ 社群爆款帶貨文案（包含強效 Call-to-Action 促銷導流用語）
4. 🏷️ 10 個高搜尋量標籤 (Hashtags)"""
                st.success("生成成功！請複製下方框內文字：")
                st.code(prompt_result, language="text")
            else:
                st.warning("請先輸入商品連結或品名！")

    # --- 功能二：AI 語音合成器 ---
    elif menu_choice == "🔊 AI 語音合成器":
        st.title("🔊 AI 帶貨語音自動生成")
        st.write("將寫好的文案直接貼在下方，一鍵轉成專業口播配音！")

        tts_text = st.text_area("請貼上口播文案（旁白）：", height=150, placeholder="例如：每天早上出門前都在發愁穿什麼？這件絕對是小資女的拯救神器...")

        if st.button("🎙️ 生成語音 (MP3)"):
            if tts_text:
                with st.spinner("語音合成中..."):
                    audio_file = "output.mp3"
                    asyncio.run(generate_speech(tts_text, audio_file))
                    st.success("語音生成完畢！")
                    st.audio(audio_file, format="audio/mp3")
                    
                    with open(audio_file, "rb") as f:
                        st.download_button(
                            label="⬇️ 下載 MP3 語音檔",
                            data=f,
                            file_name="shopee_voice.mp3",
                            mime="audio/mp3"
                        )
            else:
                st.warning("請輸入文案內容！")

if not st.session_state['logged_in']:
    st.info("👈 請先在左側欄進行 **登入** 或 **註冊帳號** 以開始使用系統。")
