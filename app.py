import streamlit as st
import requests
import json
import base64

st.set_page_config(page_title="蝦皮獨家爆款 AI 戰術系統", page_icon="🔥", layout="wide")

api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.title("🔑 API 設定")
    api_key = st.text_input("請貼上您的 Gemini API Key：", type="password")

if api_key:
    st.title("🔥 蝦皮獨家爆款 AI 戰術系統 (含動態商品展示)")
    
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
        
        btn = st.button("🚀 生成獨家戰術行銷包 + 動態商品影片", type="primary", use_container_width=True)

    with col2:
        if btn:
            with st.spinner("AI 正在分析競品痛點並生成文案..."):
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
5. 🎨 Midjourney / Runway 專用英文 Prompt
"""
                    parts = [{"text": prompt}]
                    
                    if uploaded_file:
                        bytes_data = uploaded_file.getvalue()
                        base64_img = base64.b64encode(bytes_data).decode("utf-8")
                        parts.append({
                            "inline_data": {
                                "mime_type": uploaded_file.type,
                                "data": base64_img
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

            # 動態渲染區（無須 external API，100% 成功率）
            st.divider()
            st.subheader("🎥 6. 本商品動態宣傳影片預覽")
            
            # 取得圖片 Base64
            if uploaded_file:
                img_data = base64.b64encode(uploaded_file.getvalue()).decode()
                img_src = f"data:{uploaded_file.type};base64,{img_data}"
            else:
                # 若未上傳圖片，自動生成一張商品展示圖
                image_prompt = f"commercial product shot of {product_name}, luxury studio lighting, high resolution, 4k"
                img_src = f"https://pollinations.ai/p/{image_prompt.replace(' ', '%20')}?width=800&height=450&seed=42&model=flux"

            # 嵌入 HTML5 / CSS3 3D 鏡頭動畫引擎
            html_code = f"""
            <style>
                .video-box {{
                    position: relative;
                    width: 100%;
                    max-width: 700px;
                    height: 380px;
                    overflow: hidden;
                    border-radius: 12px;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.3);
                    background: #000;
                }}
                .product-img {{
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    animation: panZoom 8s infinite alternate ease-in-out;
                }}
                .light-sweep {{
                    position: absolute;
                    top: 0; left: -100%;
                    width: 50%; height: 100%;
                    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
                    transform: skewX(-25deg);
                    animation: sweep 4s infinite ease-in-out;
                }}
                .caption-tag {{
                    position: absolute;
                    bottom: 20px;
                    left: 20px;
                    background: rgba(0,0,0,0.75);
                    color: #fff;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 14px;
                    font-family: sans-serif;
                    border: 1px solid rgba(255,255,255,0.2);
                }}
                @keyframes panZoom {{
                    0% {{ transform: scale(1.0) translate(0, 0); }}
                    100% {{ transform: scale(1.15) translate(-10px, -5px); }}
                }}
                @keyframes sweep {{
                    0% {{ left: -100%; }}
                    50% {{ left: 150%; }}
                    100% {{ left: 150%; }}
                }}
            </style>
            <div class="video-box">
                <img src="{img_src}" class="product-img">
                <div class="light-sweep"></div>
                <div class="caption-tag">🔥 {product_name} - 獨家爆款極速渲染中</div>
            </div>
            """
            st.components.v1.html(html_code, height=400)
