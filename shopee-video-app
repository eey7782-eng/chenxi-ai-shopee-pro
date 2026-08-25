import streamlit as st
import replicate
import requests
import time

st.set_page_config(page_title="AI 短影音真生成系統", page_icon="🎬", layout="wide")

st.title("🎬 真 AI 短影音生成系統 (依據指令原生運算)")

# 1. API 金鑰設定
replicate_api_token = st.secrets.get("REPLICATE_API_TOKEN", "")

if not replicate_api_token:
    replicate_api_token = st.sidebar.text_input("輸入 Replicate API Token：", type="password")
    st.sidebar.info("請至 https://replicate.com 取得免費/付費 Token")

# 2. 用戶指令輸入
product_name = st.text_input("商品名稱", "精華液")
user_prompt = st.text_area(
    "核心 AI 影片生成指令 (Prompt)",
    value=f"Use '{product_name}' as subject. Keep original packaging and details unchanged. "
          "Premium e-commerce visual, product centered on clean background, smooth full-view-to-close-up camera movement, "
          "cinematic studio lighting, 4k resolution, 9:16 vertical video.",
    height=120
)

uploaded_file = st.file_uploader("上傳商品原圖 (可選：AI 將基於此圖做動態生成)", type=["jpg", "jpeg", "png"])

# 3. 執行生成
if st.button("🚀 呼叫 AI 算力引擎生成真影片", type="primary"):
    if not replicate_api_token:
        st.error("請先設定 REPLICATE_API_TOKEN！")
    else:
        st.info("⏳ AI 算力中心正在根據您的指令逐幀算圖與合成影片，約需 1~3 分鐘...")
        
        try:
            # 設定 Client
            client = replicate.Client(api_token=replicate_api_token)
            
            # 使用可支援 Text-to-Video / Image-to-Video 的 AI 模型
            if uploaded_file:
                # 影像轉影片 (Image-to-Video)
                output = client.run(
                    "stability-ai/stable-video-diffusion:3f0457e4619da3c000508771000f484bba573dae90bf2107e6e00cd63a4f4d0c",
                    input={
                        "input_image": uploaded_file,
                        "motion_bucket_id": 127,
                        "fps": 24
                    }
                )
            else:
                # 文字轉影片 (Text-to-Video)
                output = client.run(
                    "anotherjesse/zeroscope-v2-xl:9f747673945c62801b13b84701c783929c0ee7d6f4703d2fe0a417572b049d5e",
                    input={
                        "prompt": user_prompt,
                        "num_frames": 24,
                        "fps": 24,
                        "width": 576,
                        "height": 1024  # 接近 9:16 直立比例
                    }
                )
            
            # 取得生成的 MP4 影片網址
            video_url = output[0] if isinstance(output, list) else output
            
            st.success("✅ 真 AI 影片生成成功！")
            st.video(video_url)
            
            # 提供下載連結
            video_bytes = requests.get(video_url).content
            st.download_button(
                label="📥 下載 AI 原生 MP4 影片 (可直接上傳蝦皮/TikTok)",
                data=video_bytes,
                file_name=f"{product_name}_AI_Generated.mp4",
                mime="video/mp4"
            )
            
        except Exception as e:
            st.error(f"生成失敗：{str(e)}")
