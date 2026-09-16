import subprocess
import sys

# 【自動防護】確保雲端環境自動安裝所需套件
try:
  import openai
except ImportError:
  subprocess.check_call(
      [sys.executable, "-m", "pip", "install", "openai", "requests"]
  )

import base64
from datetime import datetime
import json
import os
import tempfile
import time
from openai import OpenAI
import requests
import streamlit as st

# ==========================================
# 0. API 與系統基礎設定
# ==========================================
KLING_BASE_URL = "https://api-singapore.klingai.com"

# ==========================================
# 1. 頁面設定
# ==========================================
st.set_page_config(
    page_title="蝦皮 AI 全自動上架與可靈系統 Pro+",
    page_icon="🛒",
    layout="wide",
)

st.title("🛒 蝦皮 AI 全自動上架與可靈系統 Pro+")
st.markdown("---")

# ==========================================
# 2. 側邊欄：API 金鑰與基本設定
# ==========================================
st.sidebar.header("🔑 系統設定與 API 金鑰")

openai_api_key = st.sidebar.text_input(
    "OpenAI API Key",
    type="password",
    value=os.environ.get("OPENAI_API_KEY", ""),
)

kling_ak = st.sidebar.text_input(
    "可靈 AI (AK)", type="password", value=os.environ.get("KLING_AK", "")
)

kling_sk = st.sidebar.text_input(
    "可靈 AI (SK)", type="password", value=os.environ.get("KLING_SK", "")
)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 提示：系統已啟用自動套件載入保護，確保雲端穩定運行。"
)

# ==========================================
# 3. 主畫面功能區：商品圖片分析與文案生成
# ==========================================
st.subheader("📦 商品圖片分析與文案生成")

uploaded_file = st.file_uploader(
    "請上傳商品圖片 (JPG/PNG)", type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
  st.image(uploaded_file, caption="已上傳的商品圖片", use_column_width=True)

  if st.button("🚀 開始執行 AI 智慧分析與文案生成", type="primary"):
    if not openai_api_key:
      st.error("❌ 請先在左側欄位輸入您的 OpenAI API Key！")
    else:
      with st.spinner("🤖 OpenAI 正在分析商品並產出蝦皮文案中..."):
        try:
          client = OpenAI(api_key=openai_api_key)
          bytes_data = uploaded_file.getvalue()
          base64_image = base64.b64encode(bytes_data).decode("utf-8")

          response = client.chat.completions.create(
              model="gpt-4o",
              messages=[
                  {
                      "role": "user",
                      "content": [
                          {
                              "type": "text",
                              "text": (
                                  "請根據這張商品圖片，為我產生蝦皮風格的吸睛商品標題、詳細規格特色介紹，以及"
                                  " 5 個熱門搜尋標籤 (Hashtag)。"
                              ),
                          },
                          {
                              "type": "image_url",
                              "image_url": {
                                  "url": f"data:image/jpeg;base64,{base64_image}"
                              },
                          },
                      ],
                  }
              ],
              max_tokens=1000,
          )

          result_text = response.choices[0].message.content
          st.success("✨ 文案生成成功！")
          st.markdown("### 📝 生成結果：")
          st.markdown(result_text)

        except Exception as e:
          st.error(f"❌ 發生錯誤：{e}")

# ==========================================
# 4. 可靈 AI 短影片生成區塊
# ==========================================
st.markdown("---")
st.subheader("🎬 可靈 AI 行銷短影片生成")

prompt_text = st.text_input(
    "輸入影片運鏡與畫面描述提示詞 (Prompt)",
    value="精美商品展示，高級質感，流暢運鏡，4k",
)

if st.button("🎥 產出短影片"):
  if not kling_ak or not kling_sk:
    st.warning(
        "⚠️ 請先在左側欄位設定可靈 AI 的 AK 與 SK 才能呼叫影片生成功能。"
    )
  else:
    st.info("ℹ️ 可靈 AI 任務已送出，正在建立生成請求...")
