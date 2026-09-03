import streamlit as st
import requests
import time

KLING_API_KEY = st.secrets.get("KLING_API_KEY", "")

def create_kling_30_turbo_task(image_url: str, prompt_text: str, duration: int = 5):
    """根據 Kling 3.0 Turbo 官方規格建立圖生視頻任務"""
    url = "https://api-singapore.klingai.com/image-to-video/kling-3.0-turbo"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KLING_API_KEY}"
    }
    
    # 符合官方要求的 JSON 結構
    payload = {
        "contents": [
            {
                "type": "prompt",
                "text": prompt_text
            },
            {
                "type": "first_frame",
                "url": image_url
            }
        ],
        "settings": {
            "resolution": "1080p",
            "duration": duration  # 支援 3~15 秒
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def query_kling_task_status(task_id: str):
    """根據官方 GET /tasks 規範查詢任務進度"""
    url = f"https://api-singapore.klingai.com/tasks?task_ids={task_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KLING_API_KEY}"
    }
    
    response = requests.get(url, headers=headers)
    return response.json()

# --- Streamlit 操作介面 ---
st.subheader("🎬 Kling 3.0 Turbo 商品 AI 短影片生成")

col1, col2 = st.columns([2, 1])
with col1:
    img_url = st.text_input("商品圖片網址 (HTTP/HTTPS):", placeholder="https://your-cdn.com/product.jpg")
    prompt = st.text_area("影片動態描述 (Prompt):", value="360 degree rotation, high quality product showcase, studio lighting")
with col2:
    duration_sec = st.slider("影片秒數 (秒):", min_value=3, max_value=15, value=5)

if st.button("🚀 生成 AI 短影片"):
    if not img_url:
        st.warning("請先提供商品圖片網址！")
    else:
        with st.spinner("正在送出 Kling 3.0 Turbo 生成請求..."):
            res = create_kling_30_turbo_task(img_url, prompt, duration_sec)
        
        # 檢查是否成功建立任務 (官方回傳 code == 0 且包含 data.id)
        if res.get("code") == 0 and "data" in res and "id" in res["data"]:
            task_id = res["data"]["id"]
            st.info(f"任務建立成功！Task ID: `{task_id}`")
            
            # 輪詢狀態 (Polling)
            status_box = st.empty()
            progress_bar = st.progress(0)
            
            # 最多等待 5 分鐘 (30 次 * 10 秒)
            for attempt in range(30):
                time.sleep(10)
                query_res = query_kling_task_status(task_id)
                
                if query_res.get("code") == 0 and "data" in query_res and len(query_res["data"]) > 0:
                    task_info = query_res["data"][0]
                    status = task_info.get("status")
                    
                    status_box.text(f"生成進度中... 目前狀態：{status} ({ (attempt + 1) * 10 } 秒)")
                    progress_bar.progress(min((attempt + 1) * 3, 100))
                    
                    if status == "succeeded":
                        # 從 outputs 中提取生成好的 MP4 影片網址
                        outputs = task_info.get("outputs", [])
                        video_url = next((item["url"] for item in outputs if item.get("type") == "video"), None)
                        
                        if video_url:
                            st.success("🎉 影片生成完成！")
                            st.video(video_url)
                        break
                    elif status == "failed":
                        fail_msg = task_info.get("message", "未知原因")
                        st.error(f"生成失敗：{fail_msg}")
                        break
        else:
            st.error(f"建立任務失敗：{res.get('message', '請確認 API Key 與點數是否足夠')}")
