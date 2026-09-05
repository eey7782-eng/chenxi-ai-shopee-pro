import io
import json
import os
from datetime import datetime

import streamlit as st
from PIL import Image


# ============================================================
# 黑金剛 AI 蝦皮半自動化 2.5 PRO
# Streamlit 單檔版
# ============================================================

APP_NAME = "黑金剛 AI 蝦皮半自動化 2.5 PRO"
APP_VERSION = "2.5 PRO"


# ============================================================
# 頁面設定
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🖤",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
        radial-gradient(circle at top right, #222 0%, #090909 35%, #050505 100%);
        color: #ffffff;
    }

    [data-testid="stSidebar"] {
        background: #090909;
        border-right: 1px solid #333;
    }

    .main-title {
        font-size: 42px;
        font-weight: 900;
        letter-spacing: 2px;
        margin-bottom: 5px;
    }

    .sub-title {
        color: #aaaaaa;
        font-size: 16px;
        margin-bottom: 25px;
    }

    .card {
        background: rgba(25,25,25,0.92);
        border: 1px solid #333;
        border-radius: 18px;
        padding: 22px;
        margin-bottom: 18px;
    }

    .gold {
        color: #d7b46a;
    }

    .metric-box {
        background: #111;
        border: 1px solid #333;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
    }

    .metric-number {
        font-size: 30px;
        font-weight: 900;
    }

    .metric-label {
        color: #999;
        font-size: 14px;
    }

    .success-box {
        padding: 15px;
        border-radius: 12px;
        background: #102014;
        border: 1px solid #285d35;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Session State
# ============================================================

defaults = {
    "page": "Dashboard",
    "product_name": "",
    "category": "其他",
    "price": 999,
    "selling_points": "",
    "analysis": "",
    "shopee_copy": "",
    "tiktok_copy": "",
    "jimeng_prompt": "",
    "history": [],
    "uploaded_image": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# 商品分類
# ============================================================

def detect_category(text):
    text = text.lower()

    if any(x in text for x in ["口紅", "粉底", "面膜", "洗面", "保養", "化妝"]):
        return "保養美妝"

    if any(x in text for x in ["手機", "耳機", "充電", "平板", "3c", "電腦"]):
        return "3C"

    if any(x in text for x in ["衣服", "褲子", "鞋", "外套", "洋裝"]):
        return "服飾"

    if any(x in text for x in ["水果", "雞排", "零食", "食品", "芭樂", "鳳梨"]):
        return "食品"

    if any(x in text for x in ["家具", "收納", "清潔", "居家"]):
        return "居家生活"

    if any(x in text for x in ["汽車", "機車", "行車", "車用"]):
        return "汽機車"

    return "其他"


# ============================================================
# 商品分析
# ============================================================

def analyze_product(name, category, price, selling_points):
    if not name:
        return "請先輸入商品名稱。"

    if not category or category == "自動判斷":
        category = detect_category(name)

    points = selling_points.strip()

    result = f"""
【商品分析】

商品名稱：
{name}

商品分類：
{category}

價格：
NT$ {price}

核心賣點：
{points if points else "尚未提供"}

【行銷方向】

1. 商品第一印象
強調「{name}」的核心特色，讓消費者在第一眼就知道商品用途。

2. 蝦皮銷售方向
標題應包含商品名稱、主要特色與使用情境。
圖片應突出商品本體與主要賣點。

3. TikTok 短影音方向
前 3 秒先展示商品最吸引人的地方。
中段展示特色。
最後加入簡短行動呼籲。

4. 視覺方向
建議使用高對比、乾淨、具有商業廣告感的構圖。

5. 注意事項
不得虛構品牌、規格、成分、功效或商品資訊。
"""


    return result.strip()


# ============================================================
# 蝦皮文案
# ============================================================

def generate_shopee_copy(name, category, price, selling_points):
    points = selling_points.strip()

    return f"""
【蝦皮商品標題】

{name}｜{points if points else "熱門推薦"}｜{category}

【商品介紹】

🔥 {name}

想找一款實用又方便的商品嗎？

{name} 結合商品特色與日常使用情境，
適合想要簡單、方便入手的消費者。

✨ 商品特色
・{points if points else "特色依實際商品為準"}
・日常使用方便
・適合多種使用情境

🛒 商品資訊
商品：{name}
分類：{category}
價格：NT$ {price}

📌 購買前請依實際商品規格與頁面資訊為準。

【推薦關鍵字】

{name}
{category}
熱門商品
生活好物
推薦商品
蝦皮購物
"""


# ============================================================
# TikTok 文案
# ============================================================

def generate_tiktok_copy(name, selling_points):
    points = selling_points.strip()

    return f"""
🔥 你還沒看過這個？

今天來介紹：
{name}

✨ 最大特色
{points if points else "實用、方便、值得一看"}

如果你正在找類似商品，
這款真的可以先收藏起來！

👇 喜歡這類商品記得按讚、收藏、分享。

#TikTok
#好物推薦
#開箱
#{name.replace(" ", "")}
"""


# ============================================================
# 即夢 AI Prompt
# ============================================================

def generate_jimeng_prompt(name, category, selling_points):
    points = selling_points.strip()

    return f"""
即夢 AI 2.5 商品短影音生成指令

【影片比例】
9:16 直式短影音

【商品】
{name}

【分類】
{category}

【商品賣點】
{points if points else "以實際商品外觀為準"}

【核心規則】

1. 使用使用者提供的商品圖片作為唯一商品視覺來源。
2. 保留商品原本外觀。
3. 不改變商品形狀。
4. 不改變商品顏色。
5. 不改變品牌。
6. 不新增不存在的 LOGO。
7. 不修改包裝上的文字。
8. 不虛構商品規格。
9. 不新增不存在的配件。

【畫面】

高級商業廣告攝影風格，
商品位於畫面主要視覺中心，
背景乾淨，
光線具有電影感，
細節清楚，
質感自然。

【鏡頭】

開場：
快速但平滑地接近商品。

中段：
鏡頭緩慢環繞商品，
展示商品細節。

後段：
鏡頭回到商品正面，
形成完整商品展示。

【動態】

自然、
穩定、
電影級運鏡，
避免快速變形，
避免商品漂浮，
避免多出不相關物品。

【輸出】

TikTok / Reels / Shorts
9:16
高品質商品廣告短片。
"""


# ============================================================
# Gemini
# ============================================================

def get_gemini_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    return os.getenv("GEMINI_API_KEY")


def gemini_available():
    try:
        from google import genai
        return bool(get_gemini_key())
    except Exception:
        return False


def gemini_analyze(image_bytes, product_name):
    try:
        from google import genai
        from google.genai import types

        api_key = get_gemini_key()

        if not api_key:
            return "尚未設定 GEMINI_API_KEY。"

        client = genai.Client(api_key=api_key)

        prompt = f"""
你是黑金剛 AI 電商商品分析智能體。

請分析使用者提供的商品圖片。

商品名稱：
{product_name}

請輸出：

1. 商品外觀
2. 商品可能分類
3. 可觀察到的特色
4. 適合的電商展示方式
5. TikTok 短影音創意
6. 蝦皮商品文案方向
7. 即夢 AI 2.5 影片 Prompt

重要規則：

只能描述圖片中確實能看到的內容。
不能虛構品牌。
不能虛構規格。
不能虛構成分。
不能虛構功效。
不能把圖片外不存在的資訊當成事實。
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg",
                ),
                prompt,
            ],
        )

        return response.text

    except Exception as e:
        return f"Gemini 分析失敗：{str(e)}"


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="text-align:center;padding:15px;">
        <div style="font-size:38px;">🖤</div>
        <div style="font-size:20px;font-weight:900;">黑金剛 AI</div>
        <div style="color:#999;">蝦皮半自動化 2.5 PRO</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    menu = [
        "Dashboard",
        "商品上架工作台",
        "商品管理",
        "訂單管理",
        "數據分析",
        "AI素材庫",
        "歷史紀錄",
        "TikTok短影音",
        "蝦皮分潤管理",
    ]

    selected = st.radio(
        "功能選單",
        menu,
        index=menu.index(st.session_state.page)
        if st.session_state.page in menu
        else 0,
    )

    st.session_state.page = selected

    st.divider()

    st.caption(f"{APP_NAME}")
    st.caption(f"版本：{APP_VERSION}")


# ============================================================
# Dashboard
# ============================================================

if st.session_state.page == "Dashboard":

    st.markdown(
        '<div class="main-title">🖤 黑金剛 AI 蝦皮半自動化</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sub-title">商品分析 → AI 文案 → TikTok → 即夢 AI 2.5</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            """
            <div class="metric-box">
            <div class="metric-number">AI</div>
            <div class="metric-label">商品分析</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            """
            <div class="metric-box">
            <div class="metric-number">🛒</div>
            <div class="metric-label">蝦皮文案</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            """
            <div class="metric-box">
            <div class="metric-number">🎵</div>
            <div class="metric-label">TikTok</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            """
            <div class="metric-box">
            <div class="metric-number">🎬</div>
            <div class="metric-label">即夢 Prompt</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    st.markdown("## 🚀 開始建立商品")

    if st.button("進入商品上架工作台", use_container_width=True):
        st.session_state.page = "商品上架工作台"
        st.rerun()


# ============================================================
# 商品上架工作台
# ============================================================

elif st.session_state.page == "商品上架工作台":

    st.markdown(
        '<div class="main-title">🛒 商品上架工作台</div>',
        unsafe_allow_html=True,
    )

    st.write("輸入商品資料並上傳商品圖片。")

    col1, col2 = st.columns([1, 1])

    with col1:

        st.markdown("### 📦 商品資料")

        product_name = st.text_input(
            "商品名稱",
            value=st.session_state.product_name,
            placeholder="例如：甘草芭樂",
        )

        category = st.selectbox(
            "商品分類",
            [
                "自動判斷",
                "保養美妝",
                "3C",
                "居家生活",
                "服飾",
                "食品",
                "汽機車",
                "其他",
            ],
        )

        price = st.number_input(
            "商品價格",
            min_value=0,
            value=int(st.session_state.price),
            step=10,
        )

        selling_points = st.text_area(
            "商品賣點",
            value=st.session_state.selling_points,
            placeholder="例如：香甜、多汁、現切",
            height=120,
        )

    with col2:

        st.markdown("### 📷 商品圖片")

        uploaded = st.file_uploader(
            "上傳商品圖片",
            type=["jpg", "jpeg", "png", "webp"],
        )

        if uploaded:

            image_bytes = uploaded.getvalue()

            try:
                image = Image.open(io.BytesIO(image_bytes))

                st.session_state.uploaded_image = image_bytes

                st.image(
                    image,
                    caption="商品原圖",
                    use_container_width=True,
                )

            except Exception:
                st.error("圖片格式無法讀取。")

    st.divider()

    if st.button(
        "🧠 開始 AI 商品分析",
        type="primary",
        use_container_width=True,
    ):

        final_category = (
            detect_category(product_name)
            if category == "自動判斷"
            else category
        )

        st.session_state.product_name = product_name
        st.session_state.category = final_category
        st.session_state.price = price
        st.session_state.selling_points = selling_points

        st.session_state.analysis = analyze_product(
            product_name,
            final_category,
            price,
            selling_points,
        )

        st.session_state.shopee_copy = generate_shopee_copy(
            product_name,
            final_category,
            price,
            selling_points,
        )

        st.session_state.tiktok_copy = generate_tiktok_copy(
            product_name,
            selling_points,
        )

        st.session_state.jimeng_prompt = generate_jimeng_prompt(
            product_name,
            final_category,
            selling_points,
        )

        st.session_state.history.append(
            {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "product": product_name,
                "category": final_category,
            }
        )

        st.success("AI 商品分析完成！")

    if st.session_state.analysis:

        st.divider()

        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "🧠 商品分析",
                "🛒 蝦皮文案",
                "🎵 TikTok",
                "🎬 即夢 AI 2.5",
            ]
        )

        with tab1:
            st.text_area(
                "商品分析結果",
                st.session_state.analysis,
                height=450,
            )

        with tab2:
            st.text_area(
                "蝦皮商品文案",
                st.session_state.shopee_copy,
                height=450,
            )

        with tab3:
            st.text_area(
                "TikTok 文案",
                st.session_state.tiktok_copy,
                height=450,
            )

        with tab4:
            st.text_area(
                "即夢 AI 2.5 Prompt",
                st.session_state.jimeng_prompt,
                height=600,
            )

        if st.session_state.uploaded_image:

            st.divider()

            if gemini_available():

                if st.button(
                    "🤖 使用 Gemini 分析商品圖片",
                    use_container_width=True,
                ):

                    with st.spinner("Gemini 正在分析圖片..."):

                        result = gemini_analyze(
                            st.session_state.uploaded_image,
                            product_name,
                        )

                    st.markdown("### Gemini 分析結果")

                    st.text_area(
                        "AI 視覺分析",
                        result,
                        height=600,
                    )

            else:

                st.info(
                    "目前尚未設定 Gemini API Key。"
                    "不設定也可以使用本系統的商品分析、"
                    "蝦皮文案、TikTok 文案與即夢 Prompt 功能。"
                )


# ============================================================
# 商品管理
# ============================================================

elif st.session_state.page == "商品管理":

    st.markdown(
        '<div class="main-title">📦 商品管理</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.product_name:

        st.success(
            f"目前商品：{st.session_state.product_name}"
        )

        st.write(
            f"分類：{st.session_state.category}"
        )

        st.write(
            f"價格：NT$ {st.session_state.price}"
        )

    else:

        st.info("目前尚未建立商品。")


# ============================================================
# 訂單管理
# ============================================================

elif st.session_state.page == "訂單管理":

    st.markdown(
        '<div class="main-title">📋 訂單管理</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "目前為半自動化管理介面。"
        "後續可以接蝦皮 API 或訂單資料匯入。"
    )


# ============================================================
# 數據分析
# ============================================================

elif st.session_state.page == "數據分析":

    st.markdown(
        '<div class="main-title">📊 數據分析</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("商品數量", len(st.session_state.history))

    with c2:
        st.metric("AI 分析", len(st.session_state.history))

    with c3:
        st.metric("TikTok 素材", len(st.session_state.history))


# ============================================================
# AI 素材庫
# ============================================================

elif st.session_state.page == "AI素材庫":

    st.markdown(
        '<div class="main-title">🎨 AI 素材庫</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "這裡可以集中管理商品圖片、"
        "TikTok 文案、蝦皮文案與即夢 Prompt。"
    )

    if st.session_state.uploaded_image:

        image = Image.open(
            io.BytesIO(st.session_state.uploaded_image)
        )

        st.image(
            image,
            caption="目前商品圖片",
            width=400,
        )

    else:

        st.write("目前沒有商品圖片。")


# ============================================================
# 歷史紀錄
# ============================================================

elif st.session_state.page == "歷史紀錄":

    st.markdown(
        '<div class="main-title">🕘 歷史紀錄</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.history:

        for item in reversed(st.session_state.history):

            st.markdown(
                f"""
                <div class="card">
                <b>{item["product"]}</b><br>
                分類：{item["category"]}<br>
                時間：{item["time"]}
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        st.info("目前沒有歷史紀錄。")


# ============================================================
# TikTok
# ============================================================

elif st.session_state.page == "TikTok短影音":

    st.markdown(
        '<div class="main-title">🎵 TikTok 短影音中心</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.tiktok_copy:

        st.text_area(
            "目前 TikTok 文案",
            st.session_state.tiktok_copy,
            height=500,
        )

    else:

        st.info(
            "請先到「商品上架工作台」建立商品。"
        )


# ============================================================
# 蝦皮分潤
# ============================================================

elif st.session_state.page == "蝦皮分潤管理":

    st.markdown(
        '<div class="main-title">💰 蝦皮分潤管理</div>',
        unsafe_allow_html=True,
    )

    price = st.number_input(
        "商品售價",
        min_value=0,
        value=999,
        step=10,
    )

    cost = st.number_input(
        "商品成本",
        min_value=0,
        value=500,
        step=10,
    )

    fee = st.number_input(
        "平台及其他費用",
        min_value=0,
        value=50,
        step=10,
    )

    profit = price - cost - fee

    st.metric(
        "預估利潤",
        f"NT$ {profit}",
    )

    if profit > 0:
        st.success("目前為正毛利。")
    elif profit == 0:
        st.warning("目前沒有利潤。")
    else:
        st.error("目前為負毛利。")


# ============================================================
# Footer
# ============================================================

st.divider()

st.caption(
    f"{APP_NAME}｜{APP_VERSION}｜"
    "商品 AI 分析・蝦皮・TikTok・即夢 AI Prompt"
                               )
