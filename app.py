import streamlit as st
import requests
import time

# 讀取 API Key
KLING_API_KEY = st.secrets.get("KLING_API_KEY", "")

def create_kling_task(image_url: str, prompt_text: str):
    """步驟 1：發送圖片與提示詞給 Kling API 建立生成任務"""
    url = "https://api-singapore.klingai.com/image-to-video/kling-3.0-turbo"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KLING_API_KEY}"
    }
    payload = {
        "contents": [
            {"type": "prompt", "text": prompt_text},
            {"type": "first_frame", "url": image_url}
        ],
        "settings": {"resolution": "1080p"}
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def check_task_status(task_id: str):
    """步驟 2：查詢影片生成進度"""
    url = f"https://api-singapore.klingai.com/image-to-video/status/{task_id}"
    headers = {"Authorization": f"Bearer {KLING_API_KEY}"}
    response = requests.get(url, headers=headers)
    return response.json()

# --- Streamlit UI 介面 ---
st.title("🎬 蝦皮商品 AI 短影片生成器")

img_url = st.text_input("輸入商品圖片網址 (HTTP/HTTPS):", placeholder="https://example.com/product.jpg")
prompt = st.text_input("影片動態描述 (Prompt):", value="360 degree rotation, high quality product showcase, studio lighting")

if st.button("🚀 開始生成 AI 短影片"):
    if not img_url:
        st.warning("請先輸入商品圖片網址！")
    else:
        with st.spinner("正在向 Kling AI 發送任務請求..."):
            res = create_kling_task(img_url, prompt)
            
        if "data" in res and "task_id" in res["data"]:
            task_id = res["data"]["task_id"]
            st.info(f"任務已建立！Task ID: {task_id}，開始生成影片...")
            
            # 自動輪詢進度 (Polling)
            status_placeholder = st.empty()
            progress_bar = st.progress(0)
            
            for attempt in range(30):  # 最多等待 5 分鐘
                time.sleep(10)
                status_res = check_task_status(task_id)
                task_status = status_res.get("data", {}).get("status", "")
                
                status_placeholder.text(f"生成中... 目前狀態: {task_status} ({attempt*10}s)")
                progress_bar.progress(min((attempt + 1) * 3, 100))
                
                if task_status == "succeed":
                    video_url = status_res["data"]["result"]["videos"][0]["url"]
                    st.success("🎉 影片生成成功！")
                    st.video(video_url)  # 直接在 Streamlit 預覽生成的影片
                    break
                elif task_status == "failed":
                    st.error("影片生成失敗，請檢查提示詞或點數。")
                    break
        else:
            st.error(f"建立任務失敗：{res.get('message', '未知錯誤')}")
