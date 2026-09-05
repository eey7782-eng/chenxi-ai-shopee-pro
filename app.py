import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="即夢 AI 電商 Prompt 生成器", page_icon="🎬")
st.title("🎬 即夢 AI 電商提示詞自動生成")

# 讓你在平板上輸入 OpenAI Key (或寫死在後台)
api_key = st.sidebar.text_input("輸入 OpenAI Key", type="password")

product_desc = st.text_area("輸入商品描述（例如：復古木質手錶，放在黑色大理石上，暖光側照）", height=100)
mode = st.radio("生成類型", ["圖片背景 Prompt", "影片動態 Prompt"])

if st.button("✨ 生成即夢提示詞"):
    if not api_key:
        st.error("請先在左側欄輸入 OpenAI API Key！")
    elif not product_desc:
        st.warning("請輸入商品描述！")
    else:
        with st.spinner("OpenAI 正在思考最佳運鏡與構圖..."):
            client = OpenAI(api_key=api_key)
            
            system_prompt = (
                "你是一位專業電商視覺導演。請將商品描述轉為適合即夢 AI 的英文 Prompt。"
                "強調燈光、材質、8k 解析度。"
            )
            if mode == "影片動態 Prompt":
                system_prompt += "必須包含慢動作運鏡（slow panning, camera zoom）與動態光影描述。"

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": product_desc}
                ]
            )
            
            result_prompt = response.choices[0].message.content.strip()
            
            st.success("生成成功！請點擊下方按鈕複製，並貼到即夢 AI：")
            st.code(result_prompt, language="text")
            st.link_button("🌐 直接開啟即夢 AI 官網", "https://jimeng.jianying.com/")
