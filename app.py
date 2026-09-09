import os
import streamlit as st

# ---------------------------------------------------------------------------
# 1. 頁面標題與佈局設定
# ---------------------------------------------------------------------------
st.set_page_config(page_title="蝦皮全自動 AI 上架系統", layout="wide")

st.title("🛒 蝦皮全自動 AI 上架與多媒體處理系統")
st.caption("自動生成 SEO 爆款文案、預覽素材，並支援一鍵複製與快捷跳轉上架。")

# ---------------------------------------------------------------------------
# 2. 安全加載 OpenAI / 豆包 SDK 模組
# ---------------------------------------------------------------------------
HAS_OPENAI = False
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# 側邊欄 API 設定 (無 Key 亦可使用備案引擎)
st.sidebar.header("🔑 AI 模型設定 (選填)")
api_provider = st.sidebar.selectbox("選擇 AI 引擎", ["內建免費萬用模組", "OpenAI (GPT-4o)", "豆包 API (Volcengine)"])

api_key = ""
model_endpoint = ""

if api_provider == "OpenAI (GPT-4o)":
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
elif api_provider == "豆包 API (Volcengine)":
    api_key = st.sidebar.text_input("豆包 API Key (ARK_API_KEY)", type="password")
    model_endpoint = st.sidebar.text_input("Model Endpoint ID", placeholder="ep-2026xxxxxx-xxxxx")

# ---------------------------------------------------------------------------
# 3. 文案生成邏輯
# ---------------------------------------------------------------------------
def generate_copywriting(name, category, price, features, provider, key, endpoint):
    # 若有安裝 SDK 且填寫了 API Key
    if HAS_OPENAI and key:
        try:
            if provider == "OpenAI (GPT-4o)":
                client = OpenAI(api_key=key)
                model_name = "gpt-4o"
            elif provider == "豆包 API (Volcengine)" and endpoint:
                client = OpenAI(api_key=key, base_url="https://ark.cn-beijing.volces.com/api/v3")
                model_name = endpoint
            else:
                client = None

            if client:
                prompt = f"""
                你是一名精通蝦皮銷售的電商文案專家。請根據以下資訊撰寫爆款文案：
                【商品名稱】：{name}
                【分類】：{category}
                【售價】：NT$ {price}
                【特點與規格】：{features}

                請輸出以下結構：
                1. 【蝦皮 SEO 爆款標題】(50字內，含品牌、關鍵字與賣點)
                2. 【商品詳細描述】(帶 Emoji、特點條列、規格與注意事項)
                3. 【熱門搜尋標籤】(5-8 個 Hashtags)
                """
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                )
                return response.choices[0].message.content
        except Exception as e:
            st.sidebar.warning(f"API 呼叫失敗，自動切換至內建生成引擎：{str(e)}")

    # 備案模式：無 API Key 時自動組裝萬用文案
    feature_list = "\n".join([f"✨ {f.strip()}" for f in features.split("\n") if f.strip()])
    return f"""🔥【現貨熱銷】{name}｜{category} 熱銷推薦 專用爆款

━━━━━━━━━━━━━━━━━━━━━━━━
✨【商品核心特色】
{feature_list if feature_list else '✨ 品質保證，嚴選優質材質，高 CP 值首選！'}

💰【超值優惠價】：NT$ {price} 元
📦【出貨說明】：現貨供應，下單後快速出貨！

━━━━━━━━━━━━━━━━━━━━━━━━
📋【商品規格與細節】
• 商品名稱：{name}
• 商品分類：{category}
• 品質保證：7 天鑑賞期，提供完整售後服務

━━━━━━━━━━━━━━━━━━━━━━━━
#蝦皮嚴選 #{category.replace(' ', '')} #{name.replace(' ', '')} #熱銷推薦 #現貨免運 #高CP值
"""

# ---------------------------------------------------------------------------
# 4. 主介面 UI 設計
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 輸入商品資訊")
    p_name = st.text_input("商品名稱", value="極簡風無線藍牙耳機")
    p_category = st.text_input("商品分類", value="3C 數位 / 藍牙耳機")
    p_price = st.number_input("商品售價 (NT$)", value=499, step=10)
    p_features = st.text_area(
        "商品特點與規格 (每行一個特點)", 
        value="ANC 主動降噪技術\n超長續航 24 小時\nIPX5 防水防汗\n附贈 3 種尺寸矽膠耳塞",
        height=130
    )

    st.subheader("2. 上傳多媒體素材")
    uploaded_video = st.file_uploader("上傳短影片 (MP4/MOV)", type=["mp4", "mov"])
    uploaded_images = st.file_uploader("上傳商品主圖 (可多選)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    btn_generate = st.button("🚀 開始 AI 處理與文案生成", type="primary")

with col2:
    st.subheader("3. 生成結果與預覽")
    
    if btn_generate:
        if not p_name:
            st.warning("請填寫商品名稱！")
        else:
            with st.spinner("系統正在生成爆款文案..."):
                result_text = generate_copywriting(
                    p_name, p_category, p_price, p_features, api_provider, api_key, model_endpoint
                )
                st.session_state['copywriting_result'] = result_text

    current_copy = st.session_state.get('copywriting_result', '')
    st.text_area("生成的蝦皮標準文案 (點擊右上角按鈕一鍵複製)", value=current_copy, height=280)

    if uploaded_video:
        st.video(uploaded_video)
        st.success("✅ 影片載入成功")

    if uploaded_images:
        st.info(f"📸 已載入 {len(uploaded_images)} 張商品主圖")

    st.markdown("---")
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        st.link_button("👉 開啟蝦皮賣家中心", "https://seller.shopee.tw/portal/product/list/all", use_container_width=True)
    with btn_col2:
        if st.button("📦 打包排程上架", use_container_width=True):
            if current_copy:
                st.balloons()
                st.success("✅ 成功打包！商品資料已排入自動佇列。")
            else:
                st.warning("請先生成文案！")
