import streamlit as st
from rembg import remove
from PIL import Image, ImageOps
import requests
import io
import urllib.parse

def remove_bg(input_image):
    """使用 rembg 進行 AI 商品去背"""
    return remove(input_image)

def make_white_bg(fg_image, target_size=(1000, 1000)):
    """針對 酷澎 / momo 生成標準純白底圖"""
    fg_image = fg_image.convert("RGBA")
    
    # 建立純白背景畫布
    bg = Image.new("RGBA", target_size, (255, 255, 255, 255))
    
    # 計算商品等比例縮放 (留白 10% 避免貼邊)
    max_w, max_h = int(target_size[0] * 0.8), int(target_size[1] * 0.8)
    fg_image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    
    # 將商品居中貼上
    x = (target_size[0] - fg_image.width) // 2
    y = (target_size[1] - fg_image.height) // 2
    bg.paste(fg_image, (x, y), mask=fg_image)
    
    return bg.convert("RGB")

def make_ai_scene_bg(fg_image, prompt_text, target_size=(1024, 1024)):
    """針對 蝦皮 生成 AI 情境背景並進行合成"""
    encoded_prompt = urllib.parse.quote(f"empty studio background, {prompt_text}, soft lighting, highly detailed, no objects in center")
    bg_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={target_size[0]}&height={target_size[1]}&model=flux&nologo=true"
    
    # 下載 AI 背景圖
    res = requests.get(bg_url, timeout=15)
    bg_image = Image.open(io.BytesIO(res.content)).convert("RGBA")
    
    # 等比例縮放商品並合成至 AI 背景圖中央
    fg_image = fg_image.convert("RGBA")
    max_w, max_h = int(target_size[0] * 0.75), int(target_size[1] * 0.75)
    fg_image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    
    x = (target_size[0] - fg_image.width) // 2
    y = (target_size[1] - fg_image.height) // 2
    bg_image.paste(fg_image, (x, y), mask=fg_image)
    
    return bg_image.convert("RGB")

# --- UI 介面設定 ---
st.set_page_config(page_title="多平台商品圖自動生成器", page_icon="🛍️", layout="wide")

st.title("🛍️ 酷澎 / 蝦皮 / momo 電商主圖自動生成器")
st.caption("商品 100% 不變形 | 純白底去背 + AI 情境背景合成")

uploaded_file = st.file_uploader("請上傳原始商品照 (PNG/JPG)", type=["jpg", "png", "jpeg", "webp"])

if uploaded_file:
    raw_img = Image.open(uploaded_file)
    
    col1, col2 = st.columns(2)
    with col1:
        st.image(raw_img, caption="原始上傳照片", use_container_width=True)
    
    platform = st.radio("請選擇目標上架平台：", ["酷澎 / momo (合規純白底圖)", "蝦皮 (AI 高清情境宣傳圖)"])
    
    prompt = ""
    if "蝦皮" in platform:
        prompt = st.text_input("輸入情境背景描述 (Prompt)：", value="modern wooden table, blurred indoor living room background, warm sunlight")

    if st.button("🚀 開始自動生成主圖", type="primary"):
        with st.spinner("1/2 正在進行 AI 自動商品去背..."):
            nobg_img = remove_bg(raw_img)
            
        with st.spinner("2/2 正在排版與合成平台規格..."):
            if "酷澎" in platform:
                result_img = make_white_bg(nobg_img)
            else:
                result_img = make_ai_scene_bg(nobg_img, prompt)
                
        with col2:
            st.image(result_img, caption="生成結果 (已符合平台規範)", use_container_width=True)
            
            # 提供直接下載按鈕
            buf = io.BytesIO()
            result_img.save(buf, format="JPEG", quality=95)
            st.download_button(
                label="📥 下載符合規範的主圖",
                data=buf.getvalue(),
                file_name="product_main_image.jpg",
                mime="image/jpeg"
            )
