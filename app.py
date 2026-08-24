import streamlit as st
import requests
import json
import base64
import time

st.set_page_config(page_title="蝦皮獨家爆款 AI 戰術系統", page_icon="🔥", layout="wide")

api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.title("🔑 API 設定")
    api_key = st.text_input("請貼上您的 Gemini API Key：", type="password")

if api_key:
    st.title("🔥 蝦皮獨家爆款 AI 戰術系統 (AI 影片生成版)")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        product_name = st.text_input("商品名稱", "Acens 精華液")
        category = st.selectbox(
            "商品分類",
            ["美妝保養 / 個人護理", "3C 數碼 / 電腦周邊", "手機配件 / 各類周邊", "女裝 / 包包與服飾", "居家生活", "美食零食", "其他"]
        )
        price = st.number_input("商品價格 (NT$)", value=499)
        competitor_flaw = st.text_input("競品常見痛點/缺點", "市售常見精華液太黏膩、吸收慢、容易起屑")
        selling_points = st.text_area("本品獨家賣點", "極速吸收、專利控油成分、敏弱肌專用")
        uploaded_file = st.file_uploader("上傳商品圖片 (選填)", type=["jpg", "jpeg", "png"])
        
        btn = st.button("🚀 生成獨家行銷包 + AI 影片", type="primary", use_container_width=True)

    with col2:
        if btn:
            # 1. 生成文案與影片指令
            with st.spinner("1/2 AI 正在分析競品痛點並生成文案..."):
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
                    
                    prompt = f"""你是一位頂級電商行銷操盤手。針對以下商品：
- 名稱：{product_name}
- 分類：{category}
- 價格：NT$ {price}
- 競品痛點：{competitor_flaw}
- 本品賣點：{selling_points}

請輸出：
1. 🥊 高轉化蝦皮標題 (60字內)
2. 🎯 五感沉浸式商品描述
3. 📈 蝦皮搜尋演算法關鍵字矩陣
4. 🎬 短影音分鏡腳本
5. 🎨 一句簡短英文影片生成 Prompt (例如：Commercial macro shot of liquid drop on luxury skincare bottle, 4k, studio light)
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
                    res = requests.post(url, json=payload, timeout=90)
                    
                    if res.status_code == 200:
                        data = res.json()
                        result_text = data["candidates"][0]["content"]["parts"][0]["text"]
                        st.success("✨ 獨家戰術行銷包生成完成！")
                        st.code(result_text, language="markdown")
                    else:
                        st.error(f"API 錯誤：{res.text}")
                except Exception as e:
                    st.error(f"執行出錯：{str(e)}")

            # 2. 呼叫 AI 影片模型，現場渲染並下載影片
            st.divider()
            st.subheader("🎥 6. AI 現場運算商品動態影片")
            with st.spinner("2/2 AI 影片模型正在運算渲染中（免費伺服器生成影片約需要 20~40 秒，請稍候）..."):
                try:
                    # 使用 Hugging Face Text-to-Video 開源模型 API
                    hf_api_url = "https://api-inference.huggingface.co/models/damo-vilab/text-to-video-ms-1.7m"
                    video_prompt = f"commercial advertisement video of {product_name}, luxury lighting, liquid movement, 4k high quality"
                    
                    video_res = requests.post(
                        hf_api_url, 
                        json={"inputs": video_prompt},
                        timeout=120
                    )
                    
                    if video_res.status_code == 200 and len(video_res.content) > 1000:
                        st.success("🎉 AI 影片生成完畢！")
                        st.video(video_res.content)
                        st.caption("💡 影片已成功生成！您可以在平板上點擊右下角三個點下載，或是長按影片儲存。")
                    else:
                        st.warning("⚠️ 免費影片模型伺服器目前排隊人數較多。若未順利顯示，請等待 10 秒後再點擊一次生成按鈕。")
                except Exception as e:
                    st.info("💡 影片模型運算逾時，文案已為您完整生成。")
