import streamlit as st
import google.generativeai as genai
import os

st.set_page_config(page_title="蝦皮AI短影音生成器", layout="wide")

st.title("🎬 蝦皮商品 AI 自動剪輯與文案生成器")

# 優先自動讀取 Secrets 裡的 API Key
api_key = st.secrets.get("GEMINI_API_KEY", "")

with st.sidebar:
    st.header("⚙️ 設定")
    if api_key:
        st.success("✅ 已自動載入後台 API Key！")
    else:
        api_key = st.text_input("輸入 Gemini API Key", type="password")
    
    st.markdown("---")
    st.markdown("系統運作狀態：正常")

# 主畫面輸入區
url = st.text_input("🔗 請貼上蝦皮商品網址：", placeholder="https://shopee.tw/...")
product_desc = st.text_area("📦 商品重點賣點描述（可選填，幫助 AI 生成更精準文案）：", placeholder="例如：防潑水、超輕量、耐磨大容量...")

if st.button("🚀 開始生成短影音腳本與文案", type="primary"):
    if not api_key:
        st.error("請確認 Secrets 中已設定 GEMINI_API_KEY，或在側邊欄輸入 API Key！")
    elif not url and not product_desc:
        st.warning("請輸入蝦皮商品網址或商品賣點描述！")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""
你是一位專業的短影音電商帶貨專家。請針對以下商品資訊，設計一組適合 TikTok/Reels/Shorts 的 30 秒爆款短影音腳本與銷售文案：

【商品網址/資訊】：{url}
【商品重點賣點】：{product_desc}

請輸出：
1. 💡 **短影音腳本**（包含：畫面描述、鏡頭運鏡、旁白配音台詞、背景音樂建議）
2. 📝 **爆款社群文案**（包含：吸引人的標題、產品賣點介紹、強烈的行動呼籲 CTA、熱門 Hashtags）
"""
            with st.spinner("🤖 AI 正在為您分析商品並生成爆款腳本中..."):
                response = model.generate_content(prompt)
                st.success("✨ 生成成功！")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"生成過程發生錯誤：{e}")
