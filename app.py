import json
import os
import time
import requests
import pandas as pd
from datetime import datetime
import streamlit as st
import google.generativeai as genai
from playwright.sync_api import sync_playwright

# 常數設定
APP_NAME = "AI自動化"
APP_VERSION = "7.0 (真實 Playwright + Gemini 上架版)"

# -----------------------------------------------------------------------------
# 1. 真實 Gemini AI 邏輯
# -----------------------------------------------------------------------------
def real_gemini_transform(api_key: str, raw_text: str, price_multiplier: float) -> dict:
    """呼叫真實 Gemini API 將抓取到的文字轉為蝦皮格式"""
    if not api_key:
        st.error("❌ 請輸入有效的 Gemini API Key！")
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
        你是一位蝦皮電商爆款專家。請根據以下原始商品資訊，生成繁體中文的蝦皮文案。
        輸出必須符合 JSON 格式：
        {{
            "title": "爆款標題 (包含熱銷標籤，60字內)",
            "description": "排版漂亮、包含賣點與 Hashtag 的商品描述",
            "price": 399
        }}
        
        原始資訊：
        {raw_text}
        """
        response = model.generate_content(prompt)
        # 清理 JSON 回傳
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        data["price"] = int(data.get("price", 200) * price_multiplier)
        return data
    except Exception as e:
        st.error(f"Gemini AI 生成失敗: {str(e)}")
        return None

# -----------------------------------------------------------------------------
# 2. 真實 Playwright 網頁爬蟲
# -----------------------------------------------------------------------------
def real_scrape_url(url: str) -> str:
    """真實開啟瀏覽器抓取網頁標題與內文"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_load_state("networkidle")
            
            title = page.title()
            # 抓取頁面主要文字
            body_text = page.inner_text("body")[:1000] # 取前 1000 字
            browser.close()
            return f"標題: {title}\n內文: {body_text}"
    except Exception as e:
        st.warning(f"爬取 {url} 失敗，使用備用解析: {str(e)}")
        return f"商品網址: {url}"

# -----------------------------------------------------------------------------
# 3. 真實 Playwright 自動登入並上架至蝦皮
# -----------------------------------------------------------------------------
def real_shopee_upload(username, password, product_data):
    """真實啟動 Chrome 瀏覽器自動登入蝦皮並填表"""
    try:
        with sync_playwright() as p:
            # headless=False 讓你可以在螢幕上看到機器人操作
            browser = p.chromium.launch(headless=False, slow_mo=500)
            context = browser.new_context()
            page = context.new_page()

            # 1. 前往登入頁
            page.goto("https://seller.shopee.tw/account/signin")
            time.sleep(2)

            # 2. 自動輸入帳密
            page.fill("input[name='loginKey']", username)
            page.fill("input[name='password']", password)
            page.click("button[type='submit']")

            # 3. 預留 20 秒讓你手動過拼圖/簡訊驗證碼
            st.warning("⚠️ 機器人已開啟瀏覽器！若出現人機驗證/簡訊碼，請在跳出的 Chrome 視窗中手動完成...")
            time.sleep(20)

            # 4. 前往新增商品頁面
            page.goto("https://seller.shopee.tw/portal/product/new")
            time.sleep(3)

            # 5. 輸入商品名稱
            title_input = page.locator("input[placeholder*='商品名稱']").first
            if title_input.is_visible():
                title_input.fill(product_data["title"])

            # 6. 輸入商品描述
            desc_input = page.locator("textarea[placeholder*='商品描述']").first
            if desc_input.is_visible():
                desc_input.fill(product_data["description"])

            # 7. 輸入價格
            price_input = page.locator("input[placeholder*='價格']").first
            if price_input.is_visible():
                price_input.fill(str(product_data["price"]))

            time.sleep(5)
            browser.close()
            return True
    except Exception as e:
        st.error(f"蝦皮自動化失敗: {str(e)}")
        return False

# -----------------------------------------------------------------------------
# Streamlit UI
# -----------------------------------------------------------------------------
def main():
    st.set_page_config(page_title=APP_NAME, layout="wide")
    st.title(f"🤖 {APP_NAME} - 真實全自動上架系統")

    with st.sidebar:
        st.header("🔑 關鍵金鑰與帳號設定")
        gemini_key = st.text_input("Gemini API Key", type="password")
        shopee_user = st.text_input("蝦皮帳號")
        shopee_pass = st.text_input("蝦皮密碼", type="password")

    tab1, tab2 = st.tabs(["🚀 真實全自動執行", "📜 上架紀錄"])

    with tab1:
        urls_input = st.text_area(
            "請輸入商品網址 (一行一個)：",
            placeholder="https://example.com/item/1001\nhttps://example.com/item/1002",
            height=120
        )
        multiplier = st.number_input("自動售價倍率 (成本 × X)", value=1.5, step=0.1)

        if st.button("🔥 開始真實自動上架", type="primary", use_container_width=True):
            if not gemini_key or not shopee_user or not shopee_pass:
                st.error("❌ 請務必在左側欄位填寫 Gemini API Key、蝦皮帳號與密碼！")
                return

            urls = [u.strip() for u in urls_input.split("\n") if u.strip()]
            if not urls:
                st.warning("請輸入網址！")
                return

            for idx, url in enumerate(urls):
                st.info(f"正在真實處理第 {idx+1}/{len(urls)} 個商品...")
                
                # Step 1: 真實爬取
                raw_info = real_scrape_url(url)
                
                # Step 2: 真實 AI 轉換
                p_data = real_gemini_transform(gemini_key, raw_info, multiplier)
                
                if p_data:
                    st.write("✨ AI 成功生成資料：", p_data)
                    
                    # Step 3: 真實 Playwright 上架
                    st.info("🚀 正在啟動自動化瀏覽器上架至蝦皮...")
                    success = real_shopee_upload(shopee_user, shopee_pass, p_data)
                    
                    if success:
                        st.success(f"✅ {p_data['title']} 上架完成！")
                    else:
                        st.error("❌ 上架失敗。")

if __name__ == "__main__":
    main()
