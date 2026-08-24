import streamlit as st
import requests
import json
import base64
import time

st.set_page_config(page_title="AI 蝦皮自動化全套生成", page_icon="🛍️", layout="wide")

api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.title("🔑 API 設定")
    api_key = st.text_input("請貼上您的 Gemini API Key：", type="password")

if api_key:
    st.title("🛍️ AI 蝦皮自動化全套生成工具")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        product_name = st.text_input("商品名稱", "玻尿酸精華液")
        
        category = st.selectbox(
            "商品分類",
            [
                "美妝保養 / 個人護理",
                "3C 數碼 / 電腦周邊",
                "手機配件 / 各類周邊",
                "女裝 / 女性包包與服飾",
                "男裝 / 男性包包與服飾",
                "居家生活 / 家居用品",
                "美食 / 生鮮零食",
                "母嬰用品 / 玩具童裝",
                "運動 / 戶外休閒",
                "寵物用品",
                "汽機車零件周邊",
                "其他分類"
            ]
        )
        
        price = st.number_input("商品價格 (NT$)", value=499)
        selling_points = st.text_area("商品賣點", "強效保濕、清爽不黏膩、敏弱肌適用")
        uploaded_file = st.file_uploader("上傳商品圖片 (選填)", type=["jpg", "jpeg", "png"])
        
        btn = st.button("⚡ 執行 AI 全套生成（包含影片）", type="primary", use_container_width=True)

    with col2:
        if btn:
            # 1. 生成文案與影片 Prompt
            with st.spinner("1/2 AI 正在生成文案與影片提示詞..."):
                try:
                    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
                    
                    prompt = f"""你是一位頂級蝦皮電商與短影音行銷專家。針對以下商品資訊，請一次產生以下內容：

【商品資訊】
- 名稱：{product_name}
- 分類：{category}
- 價格：NT$ {price}
- 賣點：{selling_points}

1. 蝦皮爆款標題（含熱搜詞與 Emoji，60字以內）
2. 蝦皮商品特色描述（包含產品亮點、使用情境、售後說明）
3. 熱搜關鍵字標籤（以 # 分隔）
4. TikTok / Shopee 15秒短影音腳本
5. 短影片英文 Prompt（簡短的一句英文描述，用於 AI 生成商品展示影片，例如：A commercial shot of luxury perfume bottle, studio lighting, 4k）
"""
                    parts = [{"text": prompt}]
                    
                    if uploaded_file:
                        bytes_data = uploaded_file.getvalue()
                        base64_image = base64.b64encode(bytes_data).decode("utf-8")
                        parts.append({
                            "inline_data": {
                                "mime_type": uploaded_file.type,
                                "data": base64_image
                            }
                        })
                        
                    payload = {"contents": [{"parts": parts}]}
                    res = requests.post(url, json=payload, timeout=30)
                    
                    if res.status_code == 200:
                        data = res.json()
                        result_text = data["candidates"][0]["content"]["parts"][0]["text"]
                        st.success("✨ 文案生成成功！")
                        st.code(result_text, language="markdown")
                    else:
                        st.error(f"API 錯誤回應：{res.text}")
                except Exception as e:
                    st.error(f"執行出錯：{str(e)}")

            # 2. 自動生成動態影片並直接在網頁播放
            with st.spinner("2/2 AI 正在渲染生成短影片中（免費開源模型運算約需 15 秒）..."):
                try:
                    # 使用 Hugging Face 免費開源影片模型 API
                    hf_api_url = "https://api-inference.huggingface.co/models/damo-vilab/text-to-video-ms-1.7m"
                    video_prompt = f"commercial product photography of {product_name}, high quality, studio light, 4k"
                    
                    response = requests.post(
                        hf_api_url, 
                        json={"inputs": video_prompt},
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        st.success("🎥 AI 商品展示影片生成完畢！")
                        st.video(response.content)
                    else:
                        st.info("💡 影片生成伺服器忙碌中，請稍後再次嘗試生成影片。")
                except Exception as e:
                    st.info("💡 網頁連線逾時，文字文案已為您生成完成。")
