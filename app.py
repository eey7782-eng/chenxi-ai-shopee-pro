# ============================================================
# Gemini 最新版：Interactions API
# ============================================================

import os
import base64
import streamlit as st

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    genai = None
    HAS_GENAI = False


# ------------------------------------------------------------
# Gemini 設定
# ------------------------------------------------------------

GEMINI_MODEL = "gemini-3.7-flash"


def get_gemini_api_key():
    """從 Streamlit Secrets 或環境變數取得 API Key"""

    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        key = ""

    if key:
        return str(key).strip()

    return os.getenv("GEMINI_API_KEY", "").strip()


@st.cache_resource
def get_gemini_client():
    """建立新版 Gemini Client"""

    if not HAS_GENAI:
        return None

    api_key = get_gemini_api_key()

    if not api_key:
        return None

    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        st.session_state["gemini_error"] = str(e)
        return None


def gemini_available():
    """確認 Gemini 是否可使用"""

    if not HAS_GENAI:
        return False

    return bool(get_gemini_api_key())


# ------------------------------------------------------------
# Gemini 純文字
# ------------------------------------------------------------

def call_gemini_text(prompt, model=None):
    """
    使用 Gemini Interactions API 進行文字生成
    """

    client = get_gemini_client()

    if client is None:
        return None

    model = model or GEMINI_MODEL

    try:
        interaction = client.interactions.create(
            model=model,
            input=prompt
        )

        result = getattr(interaction, "output_text", None)

        if result:
            return result.strip()

        return None

    except Exception as e:
        st.session_state["gemini_error"] = str(e)
        return None


# ------------------------------------------------------------
# Gemini 商品圖片分析
# ------------------------------------------------------------

def call_gemini_image(
    image_bytes,
    prompt,
    mime_type="image/jpeg",
    model=None
):
    """
    使用 Gemini Interactions API
    同時傳送商品圖片 + 分析指令
    """

    client = get_gemini_client()

    if client is None:
        return None

    model = model or GEMINI_MODEL

    try:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        interaction = client.interactions.create(
            model=model,
            input=[
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image",
                    "data": image_b64,
                    "mime_type": mime_type
                }
            ]
        )

        result = getattr(interaction, "output_text", None)

        if result:
            return result.strip()

        return None

    except Exception as e:
        st.session_state["gemini_error"] = str(e)
        return None


# ------------------------------------------------------------
# 黑金剛商品分析
# ------------------------------------------------------------

def analyze_product_with_gemini(
    image_bytes,
    product_name="",
    category="",
    price=0,
    selling_points=""
):
    """
    黑金剛商品 AI 分析
    """

    prompt = f"""
你是「黑金剛 AI 蝦皮半自動化 2.5 PRO」的商品分析 AI。

請嚴格根據使用者提供的商品圖片與商品資料進行分析。

【商品名稱】
{product_name}

【商品分類】
{category}

【價格】
{price}

【賣點】
{selling_points}

請完成：

1. 商品圖片辨識
2. 商品類型
3. 商品主要外觀
4. 商品顏色
5. 商品材質
6. 商品包裝
7. 品牌資訊
8. 圖片上可讀取的文字
9. 商品主要賣點
10. 適合的蝦皮標題
11. 蝦皮商品描述
12. TikTok 開場 Hook
13. TikTok 短影音腳本
14. 即夢 AI 2.5 商品影片 Prompt

【非常重要】

商品圖片是第一優先資料來源。

不得自行虛構：

- 品牌
- Logo
- 商品規格
- 商品容量
- 商品重量
- 商品成分
- 商品功效
- 商品認證
- 商品價格
- 商品文字

如果圖片無法確認，就寫：

「圖片無法確認」

不要猜測。

如果商品圖片與使用者提供的商品名稱或資料存在衝突，
請明確標記：

「⚠️ 商品資料與圖片可能不一致」

即夢 AI 2.5 Prompt 必須：

- 保持原商品外觀
- 保持原品牌
- 保持原 Logo
- 保持原包裝
- 保持原顏色
- 保持原形狀
- 保持原材質
- 不新增不存在的文字
- 不修改品牌
- 不改變商品結構
- 不產生假的商品規格

影片比例：

9:16

風格：

高級商業商品廣告
電影級燈光
產品攝影
慢速推鏡
輕微環繞鏡頭
商品保持清晰
商品一致性優先

最後請用以下格式輸出：

【商品分析】

【圖片辨識】

【品牌】

【商品類型】

【外觀】

【顏色】

【材質】

【包裝】

【圖片文字】

【主要賣點】

【蝦皮標題】

【蝦皮商品描述】

【TikTok Hook】

【TikTok 腳本】

【即夢 AI 2.5 Prompt】

【不確定資訊】

【圖片與資料衝突檢查】
"""

    return call_gemini_image(
        image_bytes=image_bytes,
        prompt=prompt,
        mime_type="image/jpeg"
    )


# ------------------------------------------------------------
# Gemini 產生蝦皮文案
# ------------------------------------------------------------

def generate_shopee_copy_with_gemini(
    product_name,
    category,
    price,
    selling_points,
    product_analysis=""
):

    prompt = f"""
你是蝦皮電商 AI 文案專家。

商品名稱：
{product_name}

分類：
{category}

價格：
{price}

賣點：
{selling_points}

商品 AI 分析：
{product_analysis}

請產生：

【蝦皮標題】
要求：
- 繁體中文
- 適合台灣蝦皮
- 清楚
- 有搜尋關鍵字
- 不虛構商品資訊

【商品描述】
包含：
- 商品特色
- 使用情境
- 商品賣點
- 注意事項

【短版銷售文案】

【TikTok Hook】

【TikTok 15 秒腳本】

【TikTok 30 秒腳本】

不要自行增加圖片中沒有的品牌、規格、功效或認證。
"""

    return call_gemini_text(prompt)


# ------------------------------------------------------------
# Gemini 產生即夢 Prompt
# ------------------------------------------------------------

def generate_jimeng_prompt_with_gemini(
    product_name,
    category,
    product_analysis=""
):

    prompt = f"""
你是「黑金剛 AI 蝦皮半自動化 2.5 PRO」的即夢 AI 2.5 Prompt 專家。

商品：
{product_name}

分類：
{category}

商品分析：
{product_analysis}

請建立一份 9:16 商品短影音 Prompt。

核心規則：

使用者提供的商品圖片是唯一商品外觀來源。

必須保持：

1. 原始商品
2. 原始品牌
3. 原始 Logo
4. 原始包裝
5. 原始顏色
6. 原始形狀
7. 原始材質
8. 原始文字

禁止：

- 修改品牌
- 修改 Logo
- 新增不存在文字
- 改變商品形狀
- 改變商品顏色
- 虛構規格
- 虛構成分
- 虛構認證

影片：

9:16
高級商業廣告
電影級燈光
產品攝影
慢速推鏡
輕微環繞
淺景深
乾淨背景
商品主體清晰
真實材質
真實反射
高質感電商廣告

只輸出即夢 AI 2.5 Prompt。
"""

    return call_gemini_text(prompt)
