import streamlit as st
import requests
import time

# 優先讀取 Streamlit Secrets，若未設定則使用預設 Key
EVOLINK_API_KEY = st.secrets.get("EVOLINK_API_KEY", "sk-9tUrgXx1Zo7h7rQl5nDCE5b6Bae9wuhRWXbvk0QQPNDL7PLU")

def create_kling_task_evolink(image_url: str, prompt_text: str, duration: int = 5):
    """透過 EvoLink 中轉平台建立 Kling 3.0 Turbo 影片生成任務"""
    url = "https://api.evolink.ai/v1/videos/generations"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {EVOLINK_API_KEY}"
    }
    
    payload = {
        "model": "kling-v3-turbo",
        "prompt": prompt_text,
        "image_url": image_url,
        "duration": duration,
        "resolution": "1080p"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def query_task_evolink(task_id: str):
    """查詢 EvoLink 任務處理狀態"""
    url = f"https://api.evolink.ai/v1/tasks/{task_id}"
    headers = {
        "Authorization": f"Bearer {EVOLINK_API_KEY}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# --- Streamlit 頁面介面 ---
st.set_page_config(page_title="蝦皮商品 AI 短影片生成器", page_icon="🎬", layout="wide")

st.title("🎬 蝦皮商品 AI 短影片生成器")
st.caption("Powered by Kling 3.0 Turbo & EvoLink API")

col1, col2 = st.columns([3, 1])
with col1:
    img_url = st.text_input(
        "商品圖片直鏈 (HTTP/HTTPS):", 
        placeholder="https://cf.shopee.tw/file/sg-11134201-xxxxx.jpg"
    )
    prompt = st.text_area(
        "影片動態指令 (Prompt):", 
        value="360 degree product rotation, cinematic studio lighting, high resolution, smooth movement"
    )
with col2:
    duration_sec = st.slider("影片秒數", min_value=3, max_value=12, value=5)

if st.button("🚀 開始生成 AI 影片", type="primary"):
    # 阻擋蝦皮商品頁網址，提示使用者改複製圖片直鏈
    if not img_url or not img_url.startswith("http"):
        st.warning("⚠️ 請填寫正確的圖片網址！網址必須以 http:// 或 https:// 開頭。")
    elif "shopee.tw/" in img_url and not any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', 'file/']):
        st.error("❌ 您輸入的是『蝦皮商品頁連結』而非『圖片直鏈』！請在商品圖上按右鍵或長按，選擇『複製圖片位址』後再貼上。")
    elif not EVOLINK_API_KEY:
        st.error("❌ 未檢測到有效的 API Key！")
    else:
        with st.spinner("正在向 AI 引擎提交生成任務..."):
            res = create_kling_task_evolink(img_url, prompt, duration_sec)
        
        # 解析任務 ID
        task_id = res.get("id") or res.get("data", {}).get("id") or res.get("task_id")
        
        if task_id:
            st.info(f"✅ 任務已成功建立！Task ID: `{task_id}`，AI 正在繪製影片中...")
            
            status_box = st.empty()
            progress_bar = st.progress(0)
            
            # 輪詢狀態 (最多等待 5 分鐘)
            for attempt in range(30):
                time.sleep(10)
                query_res = query_task_evolink(task_id)
                
                status = query_res.get("status") or query_res.get("data", {}).get("status")
                status_box.text(f"⏳ 處理進度：{status} (已等待 {(attempt + 1) * 10} 秒)")
                progress_bar.progress(min((attempt + 1) * 4, 100))
                
                if status in ["succeeded", "completed", "SUCCESS"]:
                    # 取得生成的影片網址
                    video_url = (
                        query_res.get("video_url") 
                        or query_res.get("data", {}).get("video_url") 
                        or (query_res.get("outputs", [{}])[0].get("url") if query_res.get("outputs") else None)
                    )
                    
                    if video_url:
                        st.success("🎉 影片生成完畢！可直接下載或預覽：")
                        st.video(video_url)
                    else:
                        st.warning("任務顯示完成，但未讀取到影片網址，以下為 API 回傳的完整數據：")
                        st.json(query_res)
                    break
                elif status in ["failed", "FAILED", "error"]:
                    err_msg = query_res.get("error") or query_res.get("message") or "生成失敗，請檢查點數餘額或圖片網址"
                    st.error(f"❌ 生成失敗：{err_msg}")
                    break
        else:
            st.error(f"❌ 任務建立失敗，API 回傳結果：{res}")
