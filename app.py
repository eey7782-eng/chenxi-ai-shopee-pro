import streamlit as st
import requests
import time
import base64

# 優先讀取 Streamlit Secrets，若未設定則使用預設 Key
EVOLINK_API_KEY = st.secrets.get("EVOLINK_API_KEY", "sk-9tUrgXx1Zo7h7rQl5nDCE5b6Bae9wuhRWXbvk0QQPNDL7PLU")

def upload_image_to_free_host(uploaded_file):
    """將本地上傳的圖片轉碼並上傳至免費圖床取得直鏈 (ImgBB API)"""
    try:
        encoded_string = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
        # 使用 ImgBB 免費公開 API Key 進行轉存
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": "4c45b778e3beed5fa8b301c29665f8a0",  # 免費轉存 Key
            "image": encoded_string
        }
        res = requests.post(url, data=payload, timeout=15).json()
        if res.get("success"):
            return res["data"]["url"]
        else:
            st.error("圖片轉存失敗，請嘗試使用圖片網址或更換圖片格式。")
            return None
    except Exception as e:
        st.error(f"圖片處理出錯：{str(e)}")
        return None

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
    # 新增圖片輸入選項頁籤：上傳圖片 或 貼上網址
    tab1, tab2 = st.tabs(["📁 上傳本地商品圖片", "🔗 貼上商品圖片網址"])
    
    final_img_url = None
    
    with tab1:
        uploaded_file = st.file_uploader("請選擇商品圖片 (JPG/PNG/WEBP)", type=["jpg", "jpeg", "png", "webp"])
        if uploaded_file:
            st.image(uploaded_file, caption="預覽上傳的商品圖", width=250)
            
    with tab2:
        img_url_input = st.text_input(
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
    # 決定使用的圖片來源
    if uploaded_file is not None:
        with st.spinner("正在處理圖片並上傳至雲端..."):
            final_img_url = upload_image_to_free_host(uploaded_file)
    elif img_url_input:
        if "shopee.tw/" in img_url_input and not any(ext in img_url_input.lower() for ext in ['.jpg', '.jpeg', '.png', 'file/']):
            st.error("❌ 您輸入的是『蝦皮商品頁連結』而非『圖片直鏈』！請在商品圖上按右鍵或長按，選擇『複製圖片位址』後再貼上。")
        else:
            final_img_url = img_url_input.strip()

    # 驗證輸入與執行 API 呼叫
    if not final_img_url:
        st.warning("⚠️ 請先上傳圖片或輸入正確的圖片網址！")
    elif not EVOLINK_API_KEY:
        st.error("❌ 未檢測到有效的 API Key！")
    else:
        with st.spinner("正在向 AI 引擎提交生成任務..."):
            res = create_kling_task_evolink(final_img_url, prompt, duration_sec)
        
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
