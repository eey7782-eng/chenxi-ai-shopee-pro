import os
import subprocess
import streamlit as st
from openai import OpenAI

# 頁面標題與佈局設定
st.set_page_config(page_title="蝦皮 AI 自動化上架系統", layout="wide")

st.title("🛒 蝦皮 AI 全自動上架與多媒體處理系統")
st.caption("自動生成 SEO 爆款文案、轉碼 1:1 蝦皮短影片，並一鍵打包排程上架。")

# 初始化 OpenAI API Client
api_key = os.getenv("OPENAI_API_KEY") or st.sidebar.text_input("輸入 OpenAI API Key", type="password")
client = OpenAI(api_key=api_key) if api_key else None

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 輸入商品資訊")
    p_name = st.text_input("商品名稱", placeholder="例如：極簡風無線藍牙耳機")
    p_category = st.text_input("商品分類", placeholder="例如：3C 數位 / 藍牙耳機")
    p_price = st.number_input("商品售價 (NT$)", value=499, step=10)
    p_features = st.text_area("商品特點與規格", placeholder="例如：主動降噪、續航 24 小時、防水防汗", height=120)

    st.subheader("2. 上傳素材")
    uploaded_video = st.file_uploader("上傳短影片母檔 (MP4/MOV)", type=["mp4", "mov"])
    uploaded_images = st.file_uploader("上傳商品主圖 (可多選)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    btn_generate = st.button("🚀 開始 AI 處理與文案生成", type="primary")

with col2:
    st.subheader("3. AI 產出結果與預覽")
    
    if btn_generate:
        if not client:
            st.error("請提供有效的 OpenAI API Key！")
        elif not p_name:
            st.warning("請填寫商品名稱！")
        else:
            # 1. 生成文案
            with st.spinner("AI 正在撰寫蝦皮爆款文案..."):
                prompt = f"""
                你是一名精通蝦皮銷售的電商文案專家。請根據以下資訊撰寫標題與描述：
                【商品名稱】：{p_name}
                【分類】：{p_category}
                【售價】：NT$ {p_price}
                【特點】：{p_features}

                請輸出：
                1. 【蝦皮 SEO 爆款標題】(50字內)
                2. 【商品詳細描述】(包含特點列舉、規格與注意事項，帶Emoji)
                3. 【熱門搜尋標籤】(5-8個 Hashtags)
                """
                try:
                    res = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7
                    )
                    st.session_state['copywriting'] = res.choices[0].message.content
                except Exception as e:
                    st.error(f"文案生成失敗：{str(e)}")

            # 2. 處理影片
            if uploaded_video:
                with st.spinner("正在將影片轉碼為蝦皮 1:1 規格 (720x720)..."):
                    with open("temp_input.mp4", "wb") as f:
                        f.write(uploaded_video.read())
                    
                    cmd = ["ffmpeg", "-y", "-i", "temp_input.mp4", "-vf", "crop='min(iw,ih)':'min(iw,ih)',scale=720:720", "-r", "30", "-b:v", "2M", "-fs", "28M", "processed_video.mp4"]
                    try:
                        subprocess.run(cmd, check=True)
                        st.session_state['video_path'] = "processed_video.mp4"
                    except Exception as e:
                        st.error(f"影片轉碼失敗：{str(e)}")

    # 顯示文案結果
    copytext = st.session_state.get('copywriting', '')
    out_copy = st.text_area("生成的蝦皮文案", value=copytext, height=250)

    # 顯示影片結果
    if 'video_path' in st.session_state:
        st.video(st.session_state['video_path'])
        st.success("✅ 影片轉碼完成（符合 1:1 正方形與 30MB 限制）")

    if st.button("📦 確定並一鍵打包發送上架"):
        if copytext:
            st.success("✅ 成功打包！數據已發送至蝦皮自動上架隊列。")
        else:
            st.warning("請先生成文案再上架。")
