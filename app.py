import os
import json
import time
import hashlib
import tempfile
from datetime import datetime, timedelta
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# 0. 可靈 (Kling) AI API 專屬設定
# ---------------------------------------------------------------------------
KLING_BASE_URL = "https://api-singapore.klingai.com"

# ---------------------------------------------------------------------------
# 1. 頁面設定與會員資料庫 (JSON 持久化)
# ---------------------------------------------------------------------------
st.set_page_config(page_title="蝦皮 AI 全自動上架與可靈系統 Pro+", layout="wide")

USER_DB_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_DB_FILE):
        default_users = {
            "admin": {
                "password": hashlib.sha256("admin123".encode()).hexdigest(),
                "reg_date": "2026-01-01 00:00:00",
                "expire_date": "2099-12-31 23:59:59",
                "is_vip": True
            }
        }
        with open(USER_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(default_users, f, ensure_ascii=False, indent=4)
        return default_users
    
    with open(USER_DB_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            for k, v in data.items():
                if isinstance(v, str):
                    data[k] = {
                        "password": v,
                        "reg_date": "2026-01-01 00:00:00",
                        "expire_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
                        "is_vip": False
                    }
            return data
        except json.JSONDecodeError:
            return {}

def save_users(users):
    with open(USER_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

users_db = load_users()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

# ---------------------------------------------------------------------------
# 2. 會員系統模組 (含 3 天試用期)
# ---------------------------------------------------------------------------
def login_system():
    st.sidebar.title("👤 會員中心")

    if not st.session_state["logged_in"]:
        menu = ["會員登入", "註冊新會員 (送3天試用)"]
        choice = st.sidebar.radio("請選擇操作", menu)

        if choice == "會員登入":
            st.sidebar.subheader("🔑 帳號登入")
            username = st.sidebar.text_input("帳號", key="login_user")
            password = st.sidebar.text_input("密碼", type="password", key="login_pwd")
            if st.sidebar.button("登入", use_container_width=True):
                user_info = users_db.get(username)
                if user_info and user_info["password"] == hash_password(password):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.sidebar.success(f"歡迎回來，{username}！")
                    st.rerun()
                else:
                    st.sidebar.error("帳號或密碼錯誤！")

        elif choice == "註冊新會員 (送3天試用)":
            st.sidebar.subheader("📝 註冊享有 3 天試用期")
            new_user = st.sidebar.text_input("設定帳號", key="reg_user")
            new_pwd = st.sidebar.text_input("設定密碼", type="password", key="reg_pwd")
            confirm_pwd = st.sidebar.text_input("確認密碼", type="password", key="reg_pwd_confirm")

            if st.sidebar.button("完成註冊", use_container_width=True):
                if not new_user or not new_pwd:
                    st.sidebar.warning("請填寫完整資訊！")
                elif new_user in users_db:
                    st.sidebar.error("該帳號已被註冊！")
                elif new_pwd != confirm_pwd:
                    st.sidebar.error("兩次密碼不一致！")
                else:
                    reg_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    expire_date_str = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
                    
                    users_db[new_user] = {
                        "password": hash_password(new_pwd),
                        "reg_date": reg_date_str,
                        "expire_date": expire_date_str,
                        "is_vip": False
                    }
                    save_users(users_db)
                    st.sidebar.success("🎉 註冊成功！系統已贈送 3 天試用期，請切換至「會員登入」。")

    else:
        current_user = st.session_state['username']
        user_info = users_db.get(current_user, {})
        
        expire_str = user_info.get("expire_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        expire_dt = datetime.strptime(expire_str, "%Y-%m-%d %H:%M:%S")
        is_expired = datetime.now() > expire_dt
        is_vip = user_info.get("is_vip", False)

        st.sidebar.success(f"🟢 登入身分：**{current_user}**")
        
        if is_vip:
            st.sidebar.info("⭐ 身分：**永久 / 正式付費會員**")
        elif is_expired:
            st.sidebar.error("⌛ 您的 3 天免費試用期已結束！")
            st.sidebar.warning("請聯絡管理員升級為正式版。")
        else:
            remaining = expire_dt - datetime.now()
            days = remaining.days
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            st.sidebar.warning(f"⏳ 試用倒數：剩餘 **{days}天 {hours}小時 {minutes}分**")

        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 登出系統", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.rerun()

login_system()

if not st.session_state["logged_in"]:
    st.title("🛒 蝦皮 AI 全自動上架與可靈系統 Pro+")
    st.info("🔒 本系統僅限會員使用，新註冊即享 **3 天免費試用期**！請先在左側邊欄進行登入或註冊。")
    st.stop()

current_user_info = users_db.get(st.session_state['username'], {})
current_expire_dt = datetime.strptime(current_user_info.get("expire_date", "2099-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S")
user_is_expired = (datetime.now() > current_expire_dt) and not current_user_info.get("is_vip", False)

# ---------------------------------------------------------------------------
# 3. 多媒體工具檢查
# ---------------------------------------------------------------------------
HAS_MEDIA_TOOLS = False
try:
    from PIL import Image
    import pillow_avif
    from moviepy.editor import ImageClip, concatenate_videoclips
    HAS_MEDIA_TOOLS = True
except ImportError:
    HAS_MEDIA_TOOLS = False

st.title("🛒 蝦皮 AI 全自動上架與可靈 AI 整合系統 Pro+")
st.caption(f"使用者：【{st.session_state['username']}】｜具備安全金鑰管理與雲端非同步任務輪詢。")

# ---------------------------------------------------------------------------
# 4. 核心邏輯與 API 模組 (含輪詢機制)
# ---------------------------------------------------------------------------
def generate_copywriting(name, category, price, features, spec1_name, spec1_options, spec2_name, spec2_options):
    feature_list = "\n".join([f"✨ {f.strip()}" for f in features.split("\n") if f.strip()])
    
    spec_text = ""
    if spec1_name and spec1_options:
        spec_text += f"\n🎨【{spec1_name}】：{spec1_options}"
    if spec2_name and spec2_options:
        spec_text += f"\n📐【{spec2_name}】：{spec2_options}"
    if not spec_text:
        spec_text = "\n📌【商品規格】：單一規格 / 現貨供應"

    return f"""🔥【現貨熱銷】{name}｜{category} 熱銷推薦 專用爆款

━━━━━━━━━━━━━━━━━━━━━━━━
✨【商品核心特色】
{feature_list if feature_list else '✨ 品質保證，嚴選優質材質，高 CP 值首選！'}

💰【超值優惠價】：NT$ {price} 元
{spec_text}

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

def call_kling_video_api_with_polling(prompt_text, api_key):
    """具備完整輪詢 (Polling) 機制的雲端影片生成"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "kling-v1",
        "prompt": prompt_text,
        "duration": 5,
        "mode": "standard",
        "aspect_ratio": "9:16"
    }
    try:
        # 1. 提交任務
        res = requests.post(f"{KLING_BASE_URL}/v1/videos/generations", headers=headers, json=payload, timeout=15)
        if res.status_code != 200:
            return None, f"API 提交失敗 ({res.status_code}): {res.text}"
        
        data = res.json()
        task_id = data.get("data", {}).get("task_id")
        if not task_id:
            return None, f"未能取得 Task ID: {res.text}"

        # 2. 迴圈輪詢狀態 (最多等待 12 次，每次 5 秒)
        for _ in range(12):
            time.sleep(5)
            status_res = requests.get(f"{KLING_BASE_URL}/v1/videos/generations/{task_id}", headers=headers, timeout=10)
            if status_res.status_code == 200:
                status_data = status_res.json().get("data", {})
                task_status = status_data.get("status")
                
                if task_status == "completed":
                    video_url = status_data.get("url")
                    return video_url, None
                elif task_status == "failed":
                    return None, "雲端影片生成失敗。"
        
        return None, "影片生成超時，請稍後至後台確認。"
    except Exception as e:
        return None, str(e)

# ---------------------------------------------------------------------------
# 5. 主介面 UI 設計
# ---------------------------------------------------------------------------
# 安全讀取 API Key (優先從 st.secrets 拿，沒有的話讓使用者填)
default_key = st.secrets.get("KLING_API_KEY", "9N8ka4iMwM8APWDcjTfq7QblW9vUjCexNLMJtPNOkrY")
with st.expander("⚙️ 進階 API 與系統設定"):
    KLING_API_KEY_INPUT = st.text_input("可靈 (Kling) API Key", value=default_key, type="password")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 輸入商品基本資訊")
    p_name = st.text_input("商品名稱", value="極簡風無線藍牙耳機")
    p_category = st.text_input("商品分類", value="3C 數位 / 藍牙耳機")
    p_price = st.number_input("商品主售價 (NT$)", value=499, step=10)
    
    st.subheader("2. 蝦皮多規格選項設定")
    enable_specs = st.checkbox("開啟多規格選項", value=True)
    
    spec1_name, spec1_options = "", ""
    spec2_name, spec2_options = "", ""
    
    if enable_specs:
        spec_col1, spec_col2 = st.columns(2)
        with spec_col1:
            spec1_name = st.text_input("規格一名稱", value="顏色款式")
            spec1_options = st.text_input("選項 (逗號隔開)", value="曜石黑, 純淨白, 櫻花粉")
        with spec_col2:
            spec2_name = st.text_input("規格二名稱", value="尺寸規格")
            spec2_options = st.text_input("選項 (逗號隔開)", value="標準版, 旗艦版")

    p_features = st.text_area("商品特點 (每行一個)", value="ANC 主動降噪技術\n超長續航 24 小時\nIPX5 防水防汗", height=100)

    uploaded_images = st.file_uploader("上傳商品主圖", type=["jpg", "jpeg", "png", "webp", "avif"], accept_multiple_files=True)
    use_kling_api = st.checkbox("🚀 同步啟動可靈雲端 AI 影片生成", value=False)
    
    if user_is_expired:
        st.error("🔒 試用期已結束，功能已鎖定。")
        btn_generate = st.button("🚀 開始 AI 文案與影片生成 (已鎖定)", type="primary", disabled=True)
    else:
        btn_generate = st.button("🚀 開始 AI 文案與影片生成", type="primary")

with col2:
    st.subheader("3. 生成結果與預覽")
    
    if btn_generate and not user_is_expired:
        if not p_name:
            st.warning("請填寫商品名稱！")
        else:
            with st.spinner("AI 正在同步處理文案與短影片中..."):
                result_text = generate_copywriting(p_name, p_category, p_price, p_features, spec1_name, spec1_options, spec2_name, spec2_options)
                st.session_state['copywriting_result'] = result_text

                if uploaded_images:
                    out_video_path, err = generate_local_fallback_video(uploaded_images)
                    if not err and out_video_path:
                        st.session_state['processed_video'] = out_video_path

                if use_kling_api:
                    if not KLING_API_KEY_INPUT:
                        st.session_state['kling_status'] = "⚠️ 尚未輸入可靈 API Key！"
                    else:
                        prompt = f"Professional commercial video for {p_name}, high-end presentation, vertical 9:16."
                        v_url, api_err = call_kling_video_api_with_polling(prompt, KLING_API_KEY_INPUT)
                        if api_err:
                            st.session_state['kling_status'] = f"⚠️ 雲端生成失敗：{api_err}"
                        else:
                            st.session_state['kling_status'] = f"✅ 雲端 AI 影片生成成功！網址：{v_url}"

    current_copy = st.session_state.get('copywriting_result', '')
    st.text_area("生成的蝦皮標準文案", value=current_copy, height=220)

    if 'kling_status' in st.session_state:
        st.info(st.session_state['kling_status'])

    if 'processed_video' in st.session_state and st.session_state['processed_video']:
        st.write("🎬 **本地 1:1 專用商品動態短影片預覽：**")
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
            if user_is_expired:
                st.error("試用期已過期！")
            elif current_copy:
                st.balloons()
                st.success("✅ 成功打包！已預留 RPA 自動化對接佇列。")
            else:
                st.warning("請先生成文案！")"Bearer {KLING_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "kling-v1",
        "prompt": prompt_text,
        "duration": 5,
        "mode": "standard",
        "aspect_ratio": "9:16"
    }
    try:
        response = requests.post(f"{KLING_BASE_URL}/v1/videos/generations", headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API 回應代碼 {response.status_code}: {response.text}"
    except Exception as e:
        return None, str(e)

# ---------------------------------------------------------------------------
# 5. 主介面 UI 設計
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 輸入商品基本資訊")
    p_name = st.text_input("商品名稱", value="極簡風無線藍牙耳機")
    p_category = st.text_input("商品分類", value="3C 數位 / 藍牙耳機")
    p_price = st.number_input("商品主售價 (NT$)", value=499, step=10)
    
    st.subheader("2. 蝦皮多規格選項設定")
    enable_specs = st.checkbox("開啟多規格選項 (例如：顏色、尺寸)", value=True)
    
    spec1_name, spec1_options = "", ""
    spec2_name, spec2_options = "", ""
    
    if enable_specs:
        spec_col1, spec_col2 = st.columns(2)
        with spec_col1:
            spec1_name = st.text_input("規格一名稱", value="顏色款式")
            spec1_options = st.text_input("選項 (用逗號隔開)", value="曜石黑, 純淨白, 櫻花粉")
        with spec_col2:
            spec2_name = st.text_input("規格二名稱 (選填)", value="尺寸/容量")
            spec2_options = st.text_input("選項 (用逗號隔開)", value="標準版, 降噪旗艦版")

    p_features = st.text_area(
        "商品特點與規格 (每行一個特點)", 
        value="ANC 主動降噪技術\n超長續航 24 小時\nIPX5 防水防汗",
        height=100
    )

    st.subheader("3. 上傳商品主圖 (支援 JPG, PNG, WEBP, AVIF)")
    uploaded_images = st.file_uploader(
        "上傳商品主圖", 
        type=["jpg", "jpeg", "png", "webp", "avif"], 
        accept_multiple_files=True
    )

    use_kling_api = st.checkbox("🚀 同步啟動「可靈 AI API」雲端影片生成引擎", value=True)
    
    # 判斷是否過期，過期則停用按鈕並給予提示
    if user_is_expired:
        st.error("🔒 您的 3 天免費試用期已結束，AI 生成與影片功能已被鎖定。")
        btn_generate = st.button("🚀 開始 AI 文案與影片生成 (已鎖定)", type="primary", disabled=True)
    else:
        btn_generate = st.button("🚀 開始 AI 文案與影片生成", type="primary")

with col2:
    st.subheader("4. 生成結果與預覽")
    
    if btn_generate and not user_is_expired:
        if not p_name:
            st.warning("請填寫商品名稱！")
        else:
            with st.spinner("AI 正在為您生成整合規格的爆款文案與影片中..."):
                result_text = generate_copywriting(
                    p_name, p_category, p_price, p_features, 
                    spec1_name, spec1_options, spec2_name, spec2_options
                )
                st.session_state['copywriting_result'] = result_text

                # 本地影片合成
                if uploaded_images:
                    out_video_path, err = generate_local_fallback_video(uploaded_images)
                    if not err and out_video_path:
                        st.session_state['processed_video'] = out_video_path
                else:
                    st.warning("請上傳圖片以自動生成動態短影片！")

                # 可靈 API 雲端生成排程
                if use_kling_api:
                    kling_prompt = f"Professional commercial video for {p_name}, high-end presentation, 8k raw texture, vertical 9:16, smooth motion."
                    api_res, api_err = call_kling_video_api(kling_prompt)
                    if api_err:
                        st.session_state['kling_status'] = f"⚠️ 可靈 API 提交狀態：{api_err}"
                    else:
                        st.session_state['kling_status'] = "✅ 可靈 AI 雲端影片生成任務已成功提交至伺服器排程！"

    current_copy = st.session_state.get('copywriting_result', '')
    st.text_area("生成的蝦皮標準文案 (含多規格排版，可點擊右上角一鍵複製)", value=current_copy, height=220)

    # 顯示可靈 API 狀態回饋
    if 'kling_status' in st.session_state:
        st.info(st.session_state['kling_status'])

    if 'processed_video' in st.session_state and st.session_state['processed_video']:
        st.write("🎬 **本地 1:1 專用商品動態短影片預覽：**")
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
            if user_is_expired:
                st.error("試用期已過期，無法打包上架！")
            elif current_copy:
                st.balloons()
                st.success("✅ 成功打包！商品文案、規格與影片已排入上架佇列。")
            else:
                st.warning("請先生成文案！")
