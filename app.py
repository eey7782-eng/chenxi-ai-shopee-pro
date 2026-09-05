import io
import os
import requests
import urllib.parse
from PIL import Image, ImageEnhance, ImageFilter
from rembg import remove
from google import genai
import streamlit as st

# 設定頁面標題
st.set_page_config(page_title="電商 AI 圖片處理工具", layout="centered")
st.title("🛍️ 電商 AI 自動去背與背景生成")

# API Key 設定 (可手動輸入或由系統環境變數讀取)
GEMINI_API_KEY = st.sidebar.text_input("Gemini API Key", type="password")
SILICONFLOW_API_KEY = st.sidebar.text_input("SiliconFlow API Key", type="password")

# 核心邏輯
def build_white_bg(fg_img: Image.Image, canvas_size=(1000, 1000)) -> Image.Image:
    canvas = Image.new("RGBA", canvas_size, (255, 255, 255, 255))
    max_dim = int(canvas_size[0] * 0.8)
    fg_copy = fg_img.copy()
    fg_copy.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    x = (canvas_size[0] - fg_copy.width) // 2
    y = (canvas_size[1] - fg_copy.height) // 2
    canvas.paste(fg_copy, (x, y), mask=fg_copy)
    return canvas.convert("RGB")

# UI 上傳元件
uploaded_file = st.file_uploader("選擇上傳商品照片", type=["jpg", "jpeg", "png"])
platform = st.selectbox("選擇上架平台", ["酷澎 / momo (白底 1000x1000)", "蝦皮 (AI 背景)"])

if uploaded_file and st.button("開始處理"):
    with st.spinner("正在進行 AI 去背與合成..."):
        raw_img = Image.open(uploaded_file).convert("RGBA")
        nobg_img = remove(raw_img)
        
        if "酷澎" in platform:
            res_img = build_white_bg(nobg_img)
        else:
            # 蝦皮簡化版呈現
            res_img = build_white_bg(nobg_img)
            
        st.image(res_img, caption="處理結果", use_container_width=True)
        
        buf = io.BytesIO()
        res_img.save(buf, format="JPEG", quality=95)
        st.download_button(
            label="📥 下載處理完成圖片",
            data=buf.getvalue(),
            file_name="processed_image.jpg",
            mime="image/jpeg"
        )
