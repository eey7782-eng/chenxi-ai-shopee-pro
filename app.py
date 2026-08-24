import streamlit as st
import requests
import json
import base64

st.set_page_config(page_title="AI 蝦皮自動化", page_icon="🛍️", layout="wide")

# 優先讀取 Secrets 中的 Key
api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.title("🔑 API 設定")
    api_key = st.text_input("請貼上您的 Gemini API Key：", type="password")

if api_key:
    st.title("🛍️ AI 蝦皮自動化生成工具")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        product_name = st.text_input("商品名稱", "玻尿酸精華液")
        category = st.text_input("商品分類", "美妝保養")
        price = st.number_input("商品價格 (NT$)", value=499)
        selling_points = st.text_area("商品賣點", "強效保濕、清爽不黏膩")
        uploaded_file = st.file_uploader("上傳商品圖片 (選填)", type=["jpg", "jpeg", "png"])
        
        btn = st.button("⚡ 執行 AI 一鍵生成", type="primary", use_container_width=True)

    with col2:
        if btn:
            with st.spinner("AI 正在生成中..."):
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                    
                    prompt = f"針對商品：{product_name}，分類：{category}，價格：{price}，賣點：{selling_points}。請生成：1.爆款標題 2.商品描述 3.熱搜標籤"
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
                        st.success("✨ 生成成功！")
                        st.markdown(result_text)
                    else:
                        st.error(f"API 錯誤：{res.text}")
                except Exception as e:
                    st.error(f"發生錯誤：{str(e)}")
