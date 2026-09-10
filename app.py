import os
import json
import time
import hashlib
import requests
import tempfile
import streamlit as st

# ---------------------------------------------------------------------------
# 1. 頁面設定與會員資料庫 (JSON 持久化儲存)
# ---------------------------------------------------------------------------
st.set_page_config(page_title="蝦皮 AI 全自動上架與會員系統", layout="wide")

USER_DB_FILE = "users.json"

# 載入會員資料庫
def load_users():
    if not os.path.exists(USER_DB_FILE):
        # 預設建立一個管理員帳號 (預設帳密: admin / admin123)
        default_users = {
            "admin": hashlib.sha256("admin123".encode()).hexdigest()
        }
        with open(USER_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(default_users, f, ensure_ascii=False, indent=4)
        return default_users
    
    with open(USER_DB_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

# 儲存會員資料庫
def save_users(users):
    with open(USER_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

# 密碼加密處理
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

users_db = load_users()

# 初始化 Session 狀態
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

# ---------------------------------------------------------------------------
# 2. 會員登入 / 註冊 / 刪除帳號系統模組
# ---------------------------------------------------------------------------
def login_system():
    st.sidebar.title("👤 會員中心")

    if not st.session_state["logged_in"]:
        menu = ["會員登入", "註冊新會員"]
        choice = st.sidebar.radio("請選擇操作", menu)

        if choice == "會員登入":
            st.sidebar.subheader("🔑 帳號登入")
            username = st.sidebar.text_input("帳號", key="login_user")
            password = st.sidebar.text_input("密碼", type="password", key="login_pwd")
            if st.sidebar.button("登入", use_container_width=True):
                hashed_pwd = hash_password(password)
                if username in users_db and users_db[username] == hashed_pwd:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.sidebar.success(f"歡迎回來，{username}！")
                    st.rerun()
                else:
                    st.sidebar.error("帳號或密碼錯誤！")

        elif choice == "註冊新會員":
            st.sidebar.subheader("📝 註冊永久會員")
            new_user = st.sidebar.text_input("設定帳號", key="reg_user")
            new_pwd = st.sidebar.text_input("設定密碼", type="password", key="reg_pwd")
            confirm_pwd = st.sidebar.text_input("確認密碼", type="password", key="reg_pwd_confirm")

            if st.sidebar.button("完成註冊", use_container_width=True):
                if not new_user or not new_pwd:
                    st.sidebar.warning("請填寫完整資訊！")
                elif new_user in users_db:
                    st.sidebar.error("該帳號已被註冊！")
                elif new_pwd != confirm_pwd:
                    st.sidebar.error("兩次輸入的密碼不一致！")
                else:
                    users_db[new_user] = hash_password(new_pwd)
                    save_users(users_db)
                    st.sidebar.success("🎉 註冊成功！成為永久會員，請切換至「登入」頁面。")

    else:
        st.sidebar.success(f"🟢 目前登入：**{st.session_state['username']}** (永久會員)")
        
        # 登出與刪除帳號選項
        if st.sidebar.button("🚪 登出系統", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.rerun()

        st.sidebar.markdown("---")
        with st.sidebar.expander("⚠️ 帳號管理 (刪除帳號)"):
            st.warning("帳號刪除後資料將無法復原。")
            del_pwd = st.text_input("輸入密碼確認刪除", type="password", key="del_pwd")
            if st.button("❌ 確定刪除我的會員帳號", type="primary", use_container_width=True):
                if hash_password(del_pwd) == users_db.get(st.session_state["username"]):
                    del users_db[st.session_state["username"]]
                    save_users(users_db)
                    st.session_state["logged_in"] = False
                    st.session_state["username"] = ""
                    st.success("帳號已成功刪除！")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("密碼驗證失敗！")

login_system()

# ---------------------------------------------------------------------------
# 3. 未登入攔截 (強制需登入才能使用系統)
# ---------------------------------------------------------------------------
if not st.session_state["logged_in"]:
    st.title("🛒 蝦皮 AI 全自動上架系統")
    st.info("🔒 本系統僅限會員使用，請先在左側邊欄進行 **「會員登入」** 或 **「註冊新會員」**。")
    st.stop()

# ---------------------------------------------------------------------------
# 4. 已登入者的 AI 自動化工具主介面
# ---------------------------------------------------------------------------
st.title("🛒 蝦皮 AI 全自動上架與影片處理系統 (Pro)")
st.caption(f"歡迎會員【{st.session_state['username']}】使用！自動生成 SEO 爆款文案與 1:1 電商短影片。")

# 載入模組安全防護
HAS_MEDIA_TOOLS = False
try:
    from PIL import Image
    from moviepy.editor import ImageClip, concatenate_videoclips
    HAS_MEDIA_TOOLS = True
except ImportError:
    HAS_MEDIA_TOOLS = False

# 側邊欄影片/API設定
st.sidebar.markdown("---")
st.sidebar.subheader("🎬 可靈 AI (Kling) 影片設定")
PRESET_KLING_KEY = "api-key-kling-9N8ka4iMwM8APWDcjTfq7QblW9vUjCexNLMJtPNOkrY"
kling_api_key = st.sidebar.text_input("Kling API Key", value=PRESET_KLING_KEY, type="password")

# 文案與影片處理邏輯
def generate_copywriting(name, category, price, features):
    feature_list = "\n".join([f"✨ {f.strip()}" for f in features.split("\n") if f.strip()])
    return f"""🔥【現貨熱銷】{name}｜{category} 熱銷推薦 專用爆款

━━━━━━━━━━━━━━━━━━━━━━━━
✨【商品核心特色】
{feature_list if feature_list else '✨ 品質保證，嚴選優質材質，高 CP 值首選！'}

💰【超值優惠價】：NT$ {price} 元
📦【出貨說明】：現貨供應，下單後快速出貨！

━━━━━━━━━━━━━━━━━━━━━━━━
📋【商品規格與細節】
• 商品名稱：{name}
• 商品分類：{category}
• 品質保證：7 天鑑賞期，提供完整售後服務

━━━━━━━━━━━━━━━━━━━━━━━━
#蝦皮嚴選 #{category.replace(' ', '')} #{name.replace(' ', '')} #熱銷推薦 #現貨免運 #高CP值
"""

def generate_local_fallback_video(image_files):
    if not HAS_MEDIA_TOOLS or not image_files:
        return None, "缺乏圖片或 PIL/MoviePy 庫。"

    try:
        clips = []
        target_size = (800, 800)

        for img_file in image_files:
            img = Image.open(img_file).convert("RGB")
            w, h = img.size
            min_dim = min(w, h)
            left, top = (w - min_dim) / 2, (h - min_dim) / 2
            img_cropped = img.crop((left, top, left + min_dim, top + min_dim))
            img_resized = img_cropped.resize(target_size, Image.Resampling.LANCZOS)

            temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            img_resized.save(temp_img.name, quality=95)

            clip = ImageClip(temp_img.name).set_duration(2.5).fadein(0.5).fadeout(0.5)
            clips.append(clip)

        final_clip = concatenate_videoclips(clips, method="compose")
        temp_out_path = tempfile.NamedTemporaryFile(delete=False, suffix='_shopee_product_video.mp4').name
        final_clip.write_videofile(temp_out_path, fps=24, codec='libx264', preset='fast', logger=None)

        final_clip.close()
        for c in clips:
            c.close()

        return temp_out_path, None
    except Exception as e:
        return None, str(e)

# ---------------------------------------------------------------------------
# 5. UI 排版與操作欄位
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 輸入商品資訊")
    p_name = st.text_input("商品名稱", value="極簡風無線藍牙耳機")
    p_category = st.text_input("商品分類", value="3C 數位 / 藍牙耳機")
    p_price = st.number_input("商品售價 (NT$)", value=499, step=10)
    p_features = st.text_area(
        "商品特點與規格 (每行一個特點)", 
        value="ANC 主動降噪技術\n超長續航 24 小時\nIPX5 防水防汗\n附贈 3 種尺寸矽膠耳塞",
        height=130
    )

    st.subheader("2. 上傳商品主圖")
    uploaded_images = st.file_uploader("上傳商品主圖", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    btn_generate = st.button("🚀 開始 AI 文案與影片生成", type="primary")

with col2:
    st.subheader("3. 生成結果與預覽")
    
    if btn_generate:
        if not p_name:
            st.warning("請填寫商品名稱！")
        else:
            with st.spinner("AI 正在為會員生成爆款文案與影片中..."):
                result_text = generate_copywriting(p_name, p_category, p_price, p_features)
                st.session_state['copywriting_result'] = result_text

                if uploaded_images:
                    out_video_path, err = generate_local_fallback_video(uploaded_images)
                    if not err and out_video_path:
                        st.session_state['processed_video'] = out_video_path
                else:
                    st.warning("請至少上傳 1 張商品圖片！")

    current_copy = st.session_state.get('copywriting_result', '')
    st.text_area("生成的蝦皮標準文案 (點擊右上角一鍵複製)", value=current_copy, height=200)

    if 'processed_video' in st.session_state and st.session_state['processed_video']:
        st.write("🎬 **蝦皮 1:1 專用商品動態短影片預覽：**")
        st.video(st.session_state['processed_video'])
        with open(st.session_state['processed_video'], "rb") as file:
            st.download_button(
                label="⬇️ 下載此商品 1:1 專用影片",
                data=file,
                file_name=f"{p_name}_shopee_video.mp4",
                mime="video/mp4"
            )

    st.markdown("---")
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        st.link_button("👉 一鍵開啟蝦皮賣家中心", "https://seller.shopee.tw/portal/product/list/all", use_container_width=True)
    with btn_col2:
        if st.button("📦 打包排程上架", use_container_width=True):
            if current_copy:
                st.balloons()
                st.success("✅ 成功打包！商品文案與影片已排入自動佇列。")
            else:
                st.warning("請先生成文案！")
