import streamlit as st
import requests
import urllib.parse
import base64

def upload_image_to_free_host(uploaded_file):
    """將本地圖片上傳至 ImgBB 免費圖床取得直鏈"""
    try:
        encoded_string = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": "4c45b778e3beed5fa8b301c29665f8a0",  # 免費圖床 Key
            "image": encoded_string
        }
        res = requests.post(url, data=payload, timeout=15).json()
        if res.get("success"):
            return res["data"]["url"]
        else:
            st.error("圖片上傳失敗，請重試。")
            return None
    except Exception as e:
        st.error(f"圖片處理失敗：{str(e)}")
        return None

def generate_pollinations_image(prompt_text, init_image_url=None, width=1024, height=1024):
    """利用 Pollinations.ai API 生成 100% 免費商品宣傳圖"""
    # 組合 Prompt，若有提供原商品圖網址，加入圖生圖引導
    if init_image_url:
        full_prompt = f"Product photo based on {init_image_url}, {prompt_text}, commercial lighting, photorealistic, 4k"
    else:
        full_prompt = f"{prompt_text}, commercial product display, studio lighting, photorealistic, 4k"
    
    # URL 編碼
    encoded_prompt = urllib.parse.quote(full_prompt)
    
    # 使用 Flux 模型生成高畫質圖片
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true"
    
    return image_url

# --- Streamlit 頁面介面 ---
st.set_page_config(page_title="蝦皮商品 AI 免費海報生成器", page_icon="🎨", layout="wide")

st.title("🎨 蝦皮商品 AI 免費海報生成器")
st.caption("Powered by Pollinations.ai (100% 免費 / 免 API Key / FLUX 模型)")

col1, col2 = st.columns([3, 1])

with col1:
    tab1, tab2 = st.tabs(["📁 上傳本地商品圖", "🔗 貼上商品圖網址"])
    final_img_url = None
    
    with tab1:
        uploaded_file = st.file_uploader("請選擇商品圖片 (JPG/PNG)", type=["jpg", "jpeg", "png", "webp"])
        if uploaded_file:
            st.image(uploaded_file, caption="原商品圖預覽", width=250)
            
    with tab2:
        img_url_input = st.text_input(
            "商品圖片直鏈 (HTTP/HTTPS):", 
            placeholder="https://cf.shopee.tw/file/sg-11134201-xxxxx.jpg"
        )

    prompt = st.text_area(
        "海報風格描述 (Prompt):", 
        value="placed on a modern marble countertop, surrounded by soft warm studio lights, sleek luxury style"
    )

with col2:
    st.markdown("**圖片尺寸設定**")
    img_width = st.selectbox("寬度 (Width)", [1024, 768, 512], index=0)
    img_height = st.selectbox("高度 (Height)", [1024, 1280, 768], index=0)

if st.button("🚀 免費生成 AI 商品宣傳圖", type="primary"):
    with st.spinner("正在處理圖片與 Prompt..."):
        if uploaded_file:
            final_img_url = upload_image_to_free_host(uploaded_file)
        elif img_url_input:
            final_img_url = img_url_input.strip()

    with st.spinner("AI 正在免費繪製商品宣傳圖中..."):
        # 呼叫 Pollinations API 取得圖片網址
        result_image_url = generate_pollinations_image(
            prompt_text=prompt, 
            init_image_url=final_img_url, 
            width=img_width, 
            height=img_height
        )
        
        st.success("🎉 海報生成成功！")
        st.image(result_image_url, caption="Pollinations AI 生成結果", use_container_width=True)
        st.markdown(f"[點此開啟/下載高畫質大圖]({result_image_url})")
