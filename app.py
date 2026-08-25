import streamlit as st
import requests
import time
import base64

st.set_page_config(page_title="AI 專屬指令商品展示影片生成器", page_icon="🎬", layout="wide")

st.title("🎬 蝦皮/TikTok AI 商品立體展示影片生成器")

# 1. API 設定
replicate_api_token = st.secrets.get("REPLICATE_API_TOKEN", "")
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")

with st.sidebar:
    st.header("🔑 API 設定")
    if not replicate_api_token:
        replicate_api_token = st.text_input("Replicate API Token", type="password")
        st.caption("取得 Token 網址：https://replicate.com")
    if not gemini_api_key:
        gemini_api_key = st.text_input("Gemini API Key", type="password")

col1, col2 = st.columns([1, 1])

with col1:
    product_name = st.text_input("商品名稱", "Acens 精華液")
    selling_points = st.text_area("賣點說明", "極速吸收、專利控油、敏弱肌適用")
    
    st.divider()
    st.subheader("🎬 您的專屬商品展示指令 (Product Showcase Prompt)")
    
    # 專門針對「真實商品展示」調校的 Prompt (無縮放、純淨背景、動態光影)
    default_user_prompt = (
        f"A cinematic high-end commercial video showcasing {product_name}. "
        "The product stands centered on a luxury display pedestal with elegant studio setup. "
        "Dynamic studio lighting moving across the product bottle, highlighting textures, materials, and metallic details. "
        "Smooth cinematic pan movement, clean backdrop, shallow depth of field, 4k resolution, 9:16 vertical orientation, "
        "no camera zoom, pure product presentation, professional retail advertising style."
    )
    
    user_prompt = st.text_area("AI 影片展示指令", value=default_user_prompt, height=180)
    uploaded_file = st.file_uploader("上傳商品原圖 (AI 將依原圖生成立體展示影片)", type=["jpg", "jpeg", "png"])
    
    btn_generate = st.button("🚀 生成立體光影展示 9:16 影片", type="primary", use_container_width=True)

with col2:
    if btn_generate:
        if not replicate_api_token:
            st.error("❌ 請先在左側輸入 Replicate API Token！")
        else:
            st.info("⏳ AI 雲端算力中心正根據您的指令繪製並渲染「真立體光影展示影片」（約需 1~3 分鐘）...")
            
            try:
                headers = {
                    "Authorization": f"Token {replicate_api_token}",
                    "Content-Type": "application/json"
                }
                
                create_url = "https://api.replicate.com/v1/predictions"
                
                if uploaded_file:
                    bytes_data = uploaded_file.getvalue()
                    base64_img = f"data:{uploaded_file.type};base64,{base64.b64encode(bytes_data).decode('utf-8')}"
                    
                    payload = {
                        "version": "3f0457e4619da3c000508771000f484bba573dae90bf2107e6e00cd63a4f4d0c",
                        "input": {
                            "input_image": base64_img,
                            "motion_bucket_id": 100,
                            "fps": 24,
                            "cond_aug": 0.02
                        }
                    }
                else:
                    payload = {
                        "version": "9f747673945c62801b13b84701c783929c0ee7d6f4703d2fe0a417572b049d5e",
                        "input": {
                            "prompt": user_prompt,
                            "num_frames": 24,
                            "fps": 24,
                            "width": 576,
                            "height": 1024
                        }
                    }
                
                response = requests.post(create_url, headers=headers, json=payload)
                res_data = response.json()
                
                if response.status_code != 201:
                    st.error(f"API 建立失敗：{res_data.get('detail', res_data)}")
                else:
                    prediction_id = res_data["id"]
                    poll_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
                    
                    progress_bar = st.progress(0)
                    step_count = 0
                    
                    while True:
                        time.sleep(4)
                        step_count += 4
                        progress_bar.progress(min(step_count, 95))
                        
                        chk_res = requests.get(poll_url, headers=headers).json()
                        status = chk_res.get("status")
                        
                        if status == "succeeded":
                            progress_bar.progress(100)
                            video_output = chk_res.get("output")
                            video_url = video_output[0] if isinstance(video_output, list) else video_output
                            
                            st.success("✅ 真 AI 商品立體展示影片渲染完成！")
                            st.video(video_url)
                            
                            video_bytes = requests.get(video_url).content
                            st.download_button(
                                label="📥 下載 AI 原生展示 MP4 影片 (Shopee / TikTok 專用)",
                                data=video_bytes,
                                file_name=f"{product_name}_Showcase_9x16.mp4",
                                mime="video/mp4",
                                use_container_width=True
                            )
                            break
                        elif status in ["failed", "canceled"]:
                            st.error(f"❌ 生成失敗：{chk_res.get('error')}")
                            break
            except Exception as e:
                st.error(f"執行過程出錯：{str(e)}")
