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
    st.title("🔥 蝦皮獨家爆款 AI 戰術系統 (商品專屬動態生成)")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        product_name = st.text_input("商品名稱", "Acens")
        category = st.selectbox(
            "商品分類",
            ["美妝保養 / 個人護理", "3C 數碼 / 電腦周邊", "手機配件 / 各類周邊", "女裝 / 包包與服飾", "居家生活", "美食零食", "其他"]
        )
        price = st.number_input("商品價格 (NT$)", value=499)
        competitor_flaw = st.text_input("競品常見痛點/缺點", "市售常見精華液太黏膩、吸收慢、容易起屑")
        selling_points = st.text_area("本品獨家賣點", "極速吸收、專利控油成分、敏弱肌專用")
        uploaded_file = st.file_uploader("上傳商品圖片 (選填)", type=["jpg", "jpeg", "png"])
        
        btn = st.button("🚀 生成獨家戰術行銷包 + 專屬動態商品圖", type="primary", use_container_width=True)

    with col2:
        if btn:
            # 1. 生成文案與行銷組合
            with st.spinner("1/2 AI 正在分析競品痛點並生成獨家戰術文案..."):
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
                    
                    prompt = f"""你是一位擅長「降維打擊」與「心智占領」的頂級電商行銷操盤手。
請針對以下商品資訊，避開市面上常見的罐頭套路，產生一套極具差異化與殺傷力的蝦皮上架組合：

【商品資訊】
- 名稱：{product_name}
- 分類：{category}
- 價格：NT$ {price}
- 競品痛點：{competitor_flaw}
- 本品賣點：{selling_points}

請輸出以下 5 大獨家內容：
1. 🥊 高轉化「降維打擊」蝦皮標題 (60字內)
2. 🎯 五感沉浸式商品描述 (包含：【競品避坑指南】、【痛點解決】、【實測體驗】)
3. 📈 蝦皮搜尋演算法關鍵字矩陣
4. 🎬 TikTok / Shopee 衝動購物型 15秒黃金前3秒短影音分鏡
5. 🎨 專用英文影片生成 Prompt (請精簡為 20 字以內的英文關鍵字，專門用於商業攝影)
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

            # 2. 根據商品即時生成專屬高清商業動態視覺
            with st.spinner("2/2 正在為您的商品即時渲染專屬視覺..."):
                try:
                    image_prompt = f"commercial product shot of {product_name}, luxury studio lighting, high resolution, 4k"
                    img_url = f"https://pollinations.ai/p/{image_prompt.replace(' ', '%20')}?width=800&height=450&seed=42&model=flux"
                    
                    st.divider()
                    st.subheader("🖼️ 6. 本商品專屬 AI 商業行銷視覺")
                    st.image(img_url, caption=f"✨ 為 {product_name} 即時算出的專屬商業展示圖 (可在平板長按儲存)")
                except Exception as e:
                    st.info("💡 視覺渲染連線超時，文案已為您完整生成。")
