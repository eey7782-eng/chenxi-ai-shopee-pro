# ============================================================
# 黑金剛 AI 蝦皮半自動化 2.5 PRO
# ============================================================
# Streamlit + Gemini Interactions API
#
# 正式版
# - Gemini 3.8 Flash
# - Gemini 3.7 Flash fallback
# - Gemini 3.6 Flash fallback
# - 商品圖片 AI 分析
# - 蝦皮文案
# - TikTok
# - 即夢 AI 2.5 Prompt
# - 商品資料
# - 歷史紀錄
# - AI 素材庫
# - Dashboard
# - 手機 / 平板介面
# ============================================================

import os
import io
import json
import base64
from pathlib import Path
from datetime import datetime

import streamlit as st
from PIL import Image


# ============================================================
# APP 設定
# ============================================================

APP_NAME = "黑金剛 AI 蝦皮半自動化 2.5 PRO"
APP_VERSION = "3.0"

DATA_DIR = Path("data")
HISTORY_DIR = DATA_DIR / "history"
PRODUCT_DIR = DATA_DIR / "products"
MEDIA_DIR = DATA_DIR / "media"

for folder in [
    DATA_DIR,
    HISTORY_DIR,
    PRODUCT_DIR,
    MEDIA_DIR,
]:
    folder.mkdir(parents=True, exist_ok=True)


# ============================================================
# Gemini
# ============================================================

try:
    from google import genai

    HAS_GENAI = True

except ImportError:

    genai = None
    HAS_GENAI = False


# ============================================================
# Gemini 模型
# ============================================================

# 最新穩定模型優先
GEMINI_MODEL_CANDIDATES = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
]

DEFAULT_GEMINI_MODEL = GEMINI_MODEL_CANDIDATES[0]


# ============================================================
# Session State
# ============================================================

DEFAULT_STATE = {
    "page": "Dashboard",
    "gemini_model": "",
    "gemini_error": "",
    "analysis_result": "",
    "shopee_result": "",
    "jimeng_result": "",
    "current_product": {},
    "history": [],
}

for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# API KEY
# ============================================================

def get_gemini_api_key():

    try:

        key = st.secrets.get(
            "GEMINI_API_KEY",
            ""
        )

    except Exception:

        key = ""

    if key:
        return str(key).strip()

    return os.getenv(
        "GEMINI_API_KEY",
        ""
    ).strip()


# ============================================================
# Gemini Client
# ============================================================

@st.cache_resource
def get_gemini_client():

    if not HAS_GENAI:
        return None

    api_key = get_gemini_api_key()

    if not api_key:
        return None

    try:

        return genai.Client(
            api_key=api_key
        )

    except Exception as e:

        st.session_state["gemini_error"] = str(e)

        return None


def gemini_available():

    return (
        HAS_GENAI
        and bool(get_gemini_api_key())
    )


# ============================================================
# Gemini API
# ============================================================

def call_gemini(
    prompt,
    image_bytes=None,
    mime_type="image/jpeg",
):

    client = get_gemini_client()

    if client is None:

        st.session_state[
            "gemini_error"
        ] = "Gemini Client 無法建立。"

        return None

    last_error = ""

    for model in GEMINI_MODEL_CANDIDATES:

        try:

            if image_bytes:

                image_b64 = base64.b64encode(
                    image_bytes
                ).decode("utf-8")

                input_data = [
                    {
                        "type": "image",
                        "mime_type": mime_type,
                        "data": image_b64,
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ]

            else:

                input_data = prompt

            interaction = client.interactions.create(
                model=model,
                input=input_data,
            )

            result = getattr(
                interaction,
                "output_text",
                None,
            )

            if result:

                st.session_state[
                    "gemini_model"
                ] = model

                st.session_state[
                    "gemini_error"
                ] = ""

                return result.strip()

        except Exception as e:

            last_error = str(e)

            continue

    st.session_state[
        "gemini_error"
    ] = last_error or "Gemini 沒有回傳內容。"

    return None


# ============================================================
# 商品分析 Prompt
# ============================================================

def build_product_analysis_prompt(
    product_name,
    category,
    price,
    selling_points,
):

    return f"""
你是「黑金剛 AI 蝦皮半自動化 2.5 PRO」的商品分析 AI。

你的任務是分析使用者提供的商品圖片。

【使用者資料】

商品名稱：
{product_name}

商品分類：
{category}

商品價格：
{price}

使用者賣點：
{selling_points}

==================================================
最高優先規則
==================================================

商品圖片是商品外觀與圖片文字的第一優先資料來源。

只能使用圖片可以確認的資訊。

如果無法確認：

請寫：
「圖片無法確認」

禁止自行猜測：

品牌
Logo
規格
型號
容量
重量
尺寸
成分
功效
認證
產地
價格
圖片文字

如果使用者輸入資料與圖片明顯不一致：

請寫：

「⚠️ 商品資料與圖片可能不一致」

==================================================
請完成
==================================================

1. 商品圖片辨識
2. 商品類型
3. 商品外觀
4. 商品顏色
5. 商品材質
6. 商品包裝
7. 品牌
8. Logo
9. 圖片文字
10. 可以確認的商品賣點
11. 蝦皮標題
12. 蝦皮商品描述
13. 短版銷售文案
14. TikTok Hook
15. TikTok 15 秒腳本
16. TikTok 30 秒腳本
17. 即夢 AI 2.5 Prompt
18. 不確定資訊
19. 圖片與資料衝突檢查

==================================================
即夢 AI 2.5 Prompt 規則
==================================================

商品圖片是唯一商品外觀來源。

必須保持：

原始商品
原始品牌
原始 Logo
原始包裝
原始顏色
原始形狀
原始材質
原始文字

禁止：

修改品牌
修改 Logo
新增不存在文字
改變商品形狀
改變商品顏色
改變包裝
虛構規格
虛構成分
虛構功效
虛構認證

==================================================
影片
==================================================

比例：
9:16

風格：

高級商業商品廣告
電影級燈光
專業產品攝影
慢速推鏡
輕微環繞鏡頭
淺景深
乾淨背景
商品主體清晰
真實材質
自然反射
高質感電商廣告

==================================================
輸出格式
==================================================

【商品分析】

【圖片辨識】

【商品類型】

【品牌】

【Logo】

【外觀】

【顏色】

【材質】

【包裝】

【圖片文字】

【主要賣點】

【蝦皮標題】

【蝦皮商品描述】

【短版銷售文案】

【TikTok Hook】

【TikTok 15 秒腳本】

【TikTok 30 秒腳本】

【即夢 AI 2.5 Prompt】

【不確定資訊】

【圖片與資料衝突檢查】
"""


# ============================================================
# 蝦皮文案
# ============================================================

def build_shopee_prompt(
    product_name,
    category,
    price,
    selling_points,
    analysis,
):

    return f"""
你是台灣蝦皮電商 AI 文案專家。

商品名稱：
{product_name}

分類：
{category}

價格：
{price}

賣點：
{selling_points}

商品分析：
{analysis}

請根據以上資料製作正式電商文案。

重要：

不得新增分析中不存在的商品資訊。

不得虛構：

品牌
規格
容量
重量
成分
功效
認證
產地

請輸出：

【蝦皮標題】

繁體中文
台灣蝦皮風格
清楚
自然
加入合理搜尋關鍵字

【蝦皮商品描述】

包含：

商品特色
商品賣點
適合使用情境
購買注意事項

【短版銷售文案】

【TikTok Hook】

【TikTok 15 秒腳本】

【TikTok 30 秒腳本】
"""


# ============================================================
# 即夢 Prompt
# ============================================================

def build_jimeng_prompt(
    product_name,
    category,
    analysis,
):

    return f"""
你是「黑金剛 AI 蝦皮半自動化 2.5 PRO」
的即夢 AI 2.5 商品影片 Prompt 專家。

商品：
{product_name}

分類：
{category}

商品分析：
{analysis}

建立一份正式的商品短影音 Prompt。

==================================================
商品一致性
==================================================

使用者提供的商品圖片是唯一商品外觀來源。

必須保持：

原始商品
原始品牌
原始 Logo
原始包裝
原始顏色
原始形狀
原始材質
原始文字

禁止：

修改品牌
修改 Logo
新增不存在文字
改變商品形狀
改變商品顏色
改變包裝
虛構規格
虛構成分
虛構功效
虛構認證

==================================================
影片
==================================================

9:16

高級商業廣告
電影級燈光
專業產品攝影
慢速推鏡
輕微環繞
淺景深
乾淨背景
商品主體清晰
真實材質
自然反射
電商廣告質感

只輸出完整的即夢 AI 2.5 Prompt。
"""


# ============================================================
# 儲存歷史
# ============================================================

def save_history(
    product_name,
    category,
    analysis,
    shopee,
    jimeng,
):

    now = datetime.now()

    record = {
        "time": now.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "product_name": product_name,
        "category": category,
        "analysis": analysis,
        "shopee": shopee,
        "jimeng": jimeng,
    }

    filename = (
        HISTORY_DIR
        / f"{now.strftime('%Y%m%d_%H%M%S')}.json"
    )

    try:

        filename.write_text(
            json.dumps(
                record,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    except Exception:
        pass


# ============================================================
# CSS
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🥷",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>

html, body, [class*="css"] {
    font-family: "Noto Sans TC", sans-serif;
}

.main {
    background: #0b0b0b;
}

.block-container {
    max-width: 1400px;
    padding-top: 2rem;
}

.hero {
    padding: 25px;
    border-radius: 18px;
    border: 1px solid #292929;
    background: #111111;
    margin-bottom: 25px;
}

.hero-title {
    font-size: 32px;
    font-weight: 900;
}

.hero-sub {
    color: #999;
    margin-top: 6px;
}

.card {
    background: #141414;
    border: 1px solid #292929;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 15px;
}

.status {
    padding: 12px;
    border-radius: 12px;
    background: #151515;
    border: 1px solid #292929;
}

@media (max-width: 768px) {

    .hero-title {
        font-size: 24px;
    }

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:

    st.markdown(
        "## 🥷 黑金剛"
    )

    st.caption(
        f"AI 蝦皮半自動化 {APP_VERSION}"
    )

    st.divider()

    menu = st.radio(
        "功能",
        [
            "Dashboard",
            "商品上架工作台",
            "AI 素材庫",
            "歷史紀錄",
            "數據分析",
        ],
    )

    st.session_state["page"] = menu

    st.divider()

    st.markdown("### 🤖 Gemini")

    if not HAS_GENAI:

        st.error(
            "google-genai 未安裝"
        )

    elif not get_gemini_api_key():

        st.warning(
            "API Key 尚未設定"
        )

    else:

        st.success(
            "Gemini API 已連線"
        )

        if st.session_state[
            "gemini_model"
        ]:

            st.caption(
                "目前模型："
                + st.session_state[
                    "gemini_model"
                ]
            )


# ============================================================
# Header
# ============================================================

st.markdown(
    """
<div class="hero">

<div class="hero-title">
🥷 黑金剛 AI 蝦皮半自動化 2.5 PRO
</div>

<div class="hero-sub">
商品分析 → 蝦皮文案 → TikTok → 即夢 AI 2.5
</div>

</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# Dashboard
# ============================================================

if menu == "Dashboard":

    st.header("🏠 Dashboard")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "AI 狀態",
            "ONLINE"
            if gemini_available()
            else "OFFLINE",
        )

    with c2:
        st.metric(
            "Gemini",
            st.session_state[
                "gemini_model"
            ]
            or "AUTO",
        )

    with c3:
        st.metric(
            "商品",
            len(list(
                PRODUCT_DIR.glob("*.json")
            )),
        )

    with c4:
        st.metric(
            "歷史",
            len(list(
                HISTORY_DIR.glob("*.json")
            )),
        )

    st.divider()

    st.info(
        "進入「商品上架工作台」，"
        "上傳商品圖片即可開始 AI 商品分析。"
    )


# ============================================================
# 商品上架工作台
# ============================================================

elif menu == "商品上架工作台":

    st.header("📦 商品上架工作台")

    left, right = st.columns(
        [1, 1]
    )

    with left:

        product_name = st.text_input(
            "商品名稱",
            placeholder="例如：甘草芭樂",
        )

        category = st.selectbox(
            "商品分類",
            [
                "食品",
                "保養美妝",
                "3C",
                "居家生活",
                "服飾",
                "汽機車",
                "其他",
            ],
        )

        price = st.number_input(
            "商品價格",
            min_value=0,
            value=999,
            step=1,
        )

        selling_points = st.text_area(
            "商品賣點",
            height=130,
            placeholder=(
                "輸入你知道的商品賣點。\n"
                "AI 不會自行虛構未確認資訊。"
            ),
        )

    with right:

        uploaded = st.file_uploader(
            "上傳商品圖片",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp",
            ],
        )

        image_bytes = None
        mime_type = "image/jpeg"

        if uploaded:

            image_bytes = uploaded.getvalue()

            if uploaded.name.lower().endswith(
                ".png"
            ):
                mime_type = "image/png"

            elif uploaded.name.lower().endswith(
                ".webp"
            ):
                mime_type = "image/webp"

            else:
                mime_type = "image/jpeg"

            st.image(
                image_bytes,
                caption="商品原圖",
                use_container_width=True,
            )

    st.divider()

    analyze = st.button(
        "🚀 Gemini 開始完整商品分析",
        type="primary",
        use_container_width=True,
    )

    if analyze:

        if not gemini_available():

            st.error(
                "Gemini API 尚未設定。"
                "請在 Streamlit Secrets 加入 GEMINI_API_KEY。"
            )

        elif not image_bytes:

            st.warning(
                "請先上傳商品圖片。"
            )

        else:

            prompt = build_product_analysis_prompt(
                product_name,
                category,
                price,
                selling_points,
            )

            with st.spinner(
                "Gemini 正在分析商品圖片..."
            ):

                result = call_gemini(
                    prompt=prompt,
                    image_bytes=image_bytes,
                    mime_type=mime_type,
                )

            if result:

                st.session_state[
                    "analysis_result"
                ] = result

                st.session_state[
                    "current_product"
                ] = {
                    "name": product_name,
                    "category": category,
                    "price": price,
                    "selling_points": selling_points,
                }

                st.success(
                    "✅ 商品分析完成"
                )

            else:

                st.error(
                    "Gemini 分析失敗。"
                )


    # ========================================================
    # 分析結果
    # ========================================================

    if st.session_state[
        "analysis_result"
    ]:

        st.divider()

        st.subheader(
            "🤖 商品 AI 分析"
        )

        st.text_area(
            "Gemini 分析結果",
            st.session_state[
                "analysis_result"
            ],
            height=650,
        )

        col_a, col_b = st.columns(2)

        # ----------------------------------------------------
        # 蝦皮文案
        # ----------------------------------------------------

        with col_a:

            if st.button(
                "🛒 產生蝦皮＋TikTok",
                use_container_width=True,
            ):

                product = st.session_state[
                    "current_product"
                ]

                prompt = build_shopee_prompt(
                    product["name"],
                    product["category"],
                    product["price"],
                    product["selling_points"],
                    st.session_state[
                        "analysis_result"
                    ],
                )

                with st.spinner(
                    "正在產生電商文案..."
                ):

                    result = call_gemini(
                        prompt
                    )

                if result:

                    st.session_state[
                        "shopee_result"
                    ] = result

                    st.success(
                        "文案完成"
                    )

        # ----------------------------------------------------
        # 即夢
        # ----------------------------------------------------

        with col_b:

            if st.button(
                "🎥 產生即夢 AI 2.5 Prompt",
                use_container_width=True,
            ):

                product = st.session_state[
                    "current_product"
                ]

                prompt = build_jimeng_prompt(
                    product["name"],
                    product["category"],
                    st.session_state[
                        "analysis_result"
                    ],
                )

                with st.spinner(
                    "正在產生即夢 Prompt..."
                ):

                    result = call_gemini(
                        prompt
                    )

                if result:

                    st.session_state[
                        "jimeng_result"
                    ] = result

                    st.success(
                        "即夢 Prompt 完成"
                    )


        # ====================================================
        # 文案結果
        # ====================================================

        if st.session_state[
            "shopee_result"
        ]:

            st.subheader(
                "🛒 蝦皮／TikTok"
            )

            st.text_area(
                "電商內容",
                st.session_state[
                    "shopee_result"
                ],
                height=500,
            )

            st.download_button(
                "📥 下載蝦皮／TikTok 文案",
                data=st.session_state[
                    "shopee_result"
                ],
                file_name="shopee_tiktok.txt",
                mime="text/plain",
                use_container_width=True,
            )


        # ====================================================
        # 即夢結果
        # ====================================================

        if st.session_state[
            "jimeng_result"
        ]:

            st.subheader(
                "🎬 即夢 AI 2.5 Prompt"
            )

            st.text_area(
                "即夢 Prompt",
                st.session_state[
                    "jimeng_result"
                ],
                height=500,
            )

            st.download_button(
                "📥 下載即夢 Prompt",
                data=st.session_state[
                    "jimeng_result"
                ],
                file_name="jimeng_prompt.txt",
                mime="text/plain",
                use_container_width=True,
            )


        # ====================================================
        # 儲存商品
        # ====================================================

        if st.button(
            "💾 儲存目前商品",
            use_container_width=True,
        ):

            product = st.session_state[
                "current_product"
            ]

         
