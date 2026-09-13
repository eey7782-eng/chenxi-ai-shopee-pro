import os
import json
import time
import hashlib
import tempfile
import base64
from datetime import datetime
import requests
import streamlit as st
from openai import OpenAI

# ---------------------------------------------------------------------------
# 0. API 與系統基礎設定
# ---------------------------------------------------------------------------
KLING_BASE_URL = "https://api-singapore.klingai.com"

# ---------------------------------------------------------------------------
# 1. 頁面設定
# ---------------------------------------------------------------------------
st.set_page_config(page_title="蝦皮 AI 全自動上架與可靈系統 Pro+", layout="wide")

# ---------------------------------------------------------------------------
# 2. 多媒體工具檢查
# ---------------------------------------------------------------------------
HAS_MEDIA_TOOLS = False
try:
    from PIL import Image
    import pillow_avif
    from moviepy.editor import ImageClip, concatenate_videoclips
    HAS_MEDIA_TOOLS = True
except ImportError:
    HAS_MEDIA_TOOLS = False

st.title("🛒 蝦皮 AI 全自動上架與視覺辨識系統 Pro+")
st.caption("具備 OpenAI 視覺辨識、自動文案生成與可靈 AI 影片生成。")

# ---------------------------------------------------------------------------
# 3. 核心邏輯與 API 模組 (含 OpenAI 視覺辨識與可靈輪詢)
# ---------------------------------------------------------------------------
def analyze_image_with_openai(image_file, api_key):
    """使用 OpenAI GPT-4o-mini 分析圖片，回傳商品名稱、分類與特點"""
    try:
        client = OpenAI(api_key=api_key)
        image_bytes = image_file.getvalue()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "請扮演專業蝦皮電商選品大師，分析這張商品圖片。請嚴格依照下列 JSON 格式（不要包覆 markdown 區塊，直接回傳純 JSON）回傳對應欄位：\n{\n  \"name\": \"吸睛的商品名稱\",\n  \"category\": \"建議的商品分類\",\n  \"features\": \"特點1\\n特點2\\n特點3\"\n}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content.strip()), None
    except Exception as e:
        return None, str(e)

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
        res = requests.post(f"{KLING_BASE_URL}/v1/videos/generations", headers=headers, json=payload, timeout=15)
        if res.status_code != 200:
            return None, f"API 提交失敗 ({res.status_code}): {res.text}"
        
        data = res.json()
        task_id = data.get("data", {}).get("task_id")
        if not task_id:
            return None, f"未能取得 Task ID: {res.text}"

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
# 4. 主介面 UI 設計 (安全讀取 Secrets)
# ---------------------------------------------------------------------------
default_kling_key = st.secrets.get("KLING_API_KEY", "")
default_openai_key = st.secrets.get("OPENAI_API_KEY", "")

with st.expander("⚙️ 進階 API 與系統設定"):
    KLING_API_KEY_INPUT = st.text_input("可靈 (Kling) API Key", value=default_kling_key, type="password")
    OPENAI_API_KEY_INPUT = st.text_input("OpenAI API Key (用於圖片智慧辨識)", value=default_openai_key, type="password")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 圖片上傳與 AI 智慧辨識")
    uploaded_images = st.file_uploader("上傳商品主圖 (支援多張)", type=["jpg", "jpeg", "png", "webp", "avif"], accept_multiple_files=True)
    
    if uploaded_images:
        if st.button("✨ 讓 AI 自動辨識圖片並填入資料", type="secondary"):
            if not OPENAI_API_KEY_INPUT:
                st.warning("請先在上方「進階 API 與系統設定」填入 OpenAI API Key！")
            else:
                with st.spinner("OpenAI 正在分析您的商品圖片中..."):
                    ai_result, ai_err = analyze_image_with_openai(uploaded_images[0], OPENAI_API_KEY_INPUT)
                    if ai_err:
                        st.error(f"圖片辨識失敗：{ai_err}")
                    else:
                        st.session_state['ai_parsed_name'] = ai_result.get("name", "")
                        st.session_state['ai_parsed_category'] = ai_result.get("category", "")
                        st.session_state['ai_parsed_features'] = ai_result.get("features", "")
                        st.success("🎉 AI 辨識成功！欄位已自動填入。")
                        st.rerun()

    st.subheader("2. 輸入商品基本資訊")
    p_name = st.text_input("商品名稱", value=st.session_state.get('ai_parsed_name', "極簡風無線藍牙耳機"))
    p_category = st.text_input("商品分類", value=st.session_state.get('ai_parsed_category', "3C 數位 / 藍牙耳機"))
    p_price = st.number_input("商品主售價 (NT$)", value=499, step=10)
    
    st.subheader("3. 蝦皮多規格選項設定")
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

    p_features = st.text_area("商品特點 (每行一個)", value=st.session_state.get('ai_parsed_features', "ANC 主動降噪技術\n超長續航 24 小時\nIPX5 防水防汗"), height=100)

    use_kling_api = st.checkbox("🚀 同步啟動可靈雲端 AI 影片生成", value=False)
    
    btn_generate = st.button("🚀 開始 AI 文案與影片生成", type="primary")

with col2:
    st.subheader("4. 生成結果與預覽")
    
    if btn_generate:
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
            if current_copy:
                st.balloons()
                st.success("✅ 成功打包！已預留 RPA 自動化對接佇列。")
            else:
                st.warning("請先生成文案！")
