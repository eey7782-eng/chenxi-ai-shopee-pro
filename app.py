# ============================================================
# AI 蝦皮自動化 2.5 PRO
# 單檔 Streamlit 版本
#
# 功能：
# 1. Gemini API
# 2. 商品圖片分析
# 3. 商品標題生成
# 4. 商品描述生成
# 5. 商品關鍵字
# 6. 蝦皮上架資料
# 7. TikTok 9:16 文案
# 8. TikTok 短影音腳本
# 9. 即夢 AI 2.5 Prompt
# 10. 歷史紀錄
# 11. JSON / TXT 匯出
#
# 不使用 google-genai
# Gemini 使用 HTTP API
# ============================================================

import os
import io
import json
import base64
from datetime import datetime

import streamlit as st
from PIL import Image


# ============================================================
# APP 設定
# ============================================================

APP_NAME = "AI 蝦皮自動化"
APP_VERSION = "2.5 PRO"

DEFAULT_MODEL = "gemini-2.5-flash"

MAX_IMAGE_MB = 20
MAX_IMAGES = 8


# ============================================================
# Streamlit 設定
# ============================================================

st.set_page_config(
    page_title=f"{APP_NAME} {APP_VERSION}",
    page_icon="🛍️",
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
        radial-gradient(
            circle at 20% 0%,
            rgba(255, 90, 0, 0.10),
            transparent 28%
        ),
        #05080d;
    color: #f5f7fa;
}

#MainMenu,
footer {
    visibility: hidden;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #0a1018,
        #070b11
    );
    border-right: 1px solid rgba(255,255,255,.08);
}

.card {
    background:
        linear-gradient(
            145deg,
            #101923,
            #090f17
        );
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 14px;
}

.title {
    font-size: 26px;
    font-weight: 900;
}

.sub {
    color: #8995a4;
    font-size: 12px;
}

.section {
    font-size: 18px;
    font-weight: 900;
    margin: 14px 0 10px 0;
}

.badge {
    display: inline-block;
    margin-left: 8px;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 11px;
    color: #ff9d52;
    border: 1px solid #ff6a00;
    background: rgba(255,90,0,.1);
}

.metric {
    background:
        linear-gradient(
            145deg,
            #111a25,
            #0b1119
        );
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 13px;
    padding: 14px;
    min-height: 82px;
}

.metric-label {
    font-size: 11px;
    color: #8995a4;
}

.metric-value {
    font-size: 21px;
    font-weight: 900;
    margin-top: 4px;
}

.orange {
    color: #ff6a00;
}

.green {
    color: #50d890;
}

.blue {
    color: #4ab7ff;
}

.purple {
    color: #b28cff;
}

.workflow {
    display: flex;
    gap: 8px;
    align-items: center;
    background: #0b121b;
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 14px;
    padding: 12px;
    margin-bottom: 14px;
    overflow-x: auto;
}

.step {
    min-width: 120px;
    flex: 1;
    background: #101923;
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 11px;
    padding: 10px;
}

.step-icon {
    font-size: 22px;
}

.step-title {
    font-size: 13px;
    font-weight: 800;
}

.step-desc {
    font-size: 10px;
    color: #7e8a99;
}

.arrow {
    color: #ff6a00;
    font-size: 20px;
    font-weight: bold;
}

.check {
    color: #49d98c;
}

.tag {
    display: inline-block;
    padding: 5px 9px;
    margin: 3px;
    background: #172331;
    border: 1px solid #293a4b;
    border-radius: 7px;
    color: #b8c5d2;
    font-size: 11px;
}

.stButton > button {
    border-radius: 8px !important;
    background: #111a24 !important;
    color: #fff !important;
    font-weight: 700 !important;
    border: 1px solid rgba(255,255,255,.12) !important;
}

.stButton > button:hover {
    border-color: #ff6a00 !important;
    color: #ff8b42 !important;
}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea {
    background: #0b121b !important;
    color: #fff !important;
    border-radius: 8px !important;
}

div[data-baseweb="select"] > div {
    background: #0b121b !important;
    color: #fff !important;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

def init_state():

    defaults = {
        "page": "商品上架工作台",

        "product_name": "",
        "category": "美妝保養",
        "price": 499,
        "stock": 100,
        "condition": "全新",
        "selling_points": "",

        "images": [],

        "generated": False,

        "analysis": "",
        "title": "",
        "description": "",
        "keywords": "",
        "selling_point_result": "",

        "tiktok": "",
        "tiktok_script": "",
        "jimeng": "",

        "shopee_data": {},

        "history": [],

        "published": 0,

        "gemini_key": "",
        "gemini_model": DEFAULT_MODEL,

        "api_status": "尚未測試",
        "last_error": "",
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


init_state()


# ============================================================
# Gemini API Key
# ============================================================

def get_api_key():

    key = st.session_state.get("gemini_key", "").strip()

    if key:
        return key

    try:
        secret_key = st.secrets.get("GEMINI_API_KEY", "")

        if secret_key:
            return str(secret_key).strip()

    except Exception:
        pass

    env_key = os.getenv("GEMINI_API_KEY", "")

    return env_key.strip()


# ============================================================
# Gemini HTTP API
# ============================================================

def gemini_request(contents):

    api_key = get_api_key()

    if not api_key:

        return {
            "ok": False,
            "error": "尚未設定 Gemini API Key"
        }

    model = (
        st.session_state.get(
            "gemini_model",
            DEFAULT_MODEL
        )
        or DEFAULT_MODEL
    ).strip()

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{model}:generateContent"
        f"?key={api_key}"
    )

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 5000,
        }
    }

    try:

        import urllib.request
        import urllib.error

        data = json.dumps(
            payload,
            ensure_ascii=False
        ).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json"
            },
            method="POST",
        )

        with urllib.request.urlopen(
            request,
            timeout=90
        ) as response:

            raw = response.read().decode(
                "utf-8",
                errors="replace"
            )

        result = json.loads(raw)

        text = extract_gemini_text(result)

        if not text:

            return {
                "ok": False,
                "error": "Gemini 沒有回傳文字內容"
            }

        st.session_state.api_status = "Gemini API 正常"

        return {
            "ok": True,
            "text": text
        }

    except urllib.error.HTTPError as e:

        try:
            error_body = e.read().decode(
                "utf-8",
                errors="replace"
            )
        except Exception:
            error_body = ""

        message = explain_http_error(
            e.code,
            error_body
        )

        st.session_state.api_status = "API 錯誤"
        st.session_state.last_error = message

        return {
            "ok": False,
            "error": message
        }

    except Exception as e:

        message = (
            "Gemini 連線失敗："
            + str(e)
        )

        st.session_state.api_status = "連線失敗"
        st.session_state.last_error = message

        return {
            "ok": False,
            "error": message
        }


# ============================================================
# Gemini 回應解析
# ============================================================

def extract_gemini_text(result):

    try:

        candidates = result.get(
            "candidates",
            []
        )

        if not candidates:
            return ""

        candidate = candidates[0]

        content = candidate.get(
            "content",
            {}
        )

        parts = content.get(
            "parts",
            []
        )

        texts = []

        for part in parts:

            if isinstance(part, dict):

                text = part.get("text")

                if text:
                    texts.append(text)

        return "\n".join(texts).strip()

    except Exception:

        return ""


# ============================================================
# Gemini 錯誤說明
# ============================================================

def explain_http_error(code, body):

    body_lower = body.lower()

    if code == 400:
        return (
            "Gemini API 400：請檢查 API Key、"
            "模型名稱或請求格式。"
        )

    if code == 401:
        return (
            "Gemini API 401：API Key 無效，"
            "請重新建立或確認 Gemini API Key。"
        )

    if code == 403:
        return (
            "Gemini API 403：API Key 沒有權限，"
            "請確認 Gemini API 是否已啟用。"
        )

    if code == 404:
        return (
            "Gemini API 404：目前設定的模型不存在或不可用。"
            "可以把模型改成 gemini-2.5-flash。"
        )

    if code == 429:
        return (
            "Gemini API 429：目前超過使用限制或配額。"
        )

    if code >= 500:
        return (
            f"Gemini 伺服器錯誤 HTTP {code}。"
        )

    if "quota" in body_lower:
        return (
            "Gemini API 配額不足。"
        )

    return (
        f"Gemini API 發生 HTTP {code} 錯誤。"
    )


# ============================================================
# 圖片轉 Gemini
# ============================================================

def image_to_part(uploaded_file):

    data = uploaded_file.getvalue()

    if not data:
        return None

    if len(data) > MAX_IMAGE_MB * 1024 * 1024:
        return None

    mime = uploaded_file.type

    if not mime:
        mime = "image/jpeg"

    encoded = base64.b64encode(
        data
    ).decode("utf-8")

    return {
        "inline_data": {
            "mime_type": mime,
            "data": encoded
        }
    }


# ============================================================
# 商品名稱
# ============================================================

def current_product_name():

    name = (
        st.session_state
        .get("product_name", "")
        .strip()
    )

    if name:
        return name

    return "我的商品"


# ============================================================
# 本地預設內容
# ============================================================

def local_title():

    return (
        f"{current_product_name()}｜"
        f"高品質商品｜日常使用推薦"
    )


def local_description():

    name = current_product_name()

    return f"""【商品名稱】
{name}

【商品介紹】
{name}，適合日常使用。

【商品特色】
✓ 商品資訊清楚
✓ 方便日常使用
✓ 商品包裝以實際圖片為準
✓ 商品規格以賣場實際資訊為準

【注意事項】
實際商品資訊、規格、容量、顏色及包裝，
請以商品實際收到的商品為準。
"""


def local_keywords():

    return (
        "商品推薦,日常用品,"
        "熱門商品,生活好物,"
        "蝦皮購物"
    )


def local_tiktok():

    name = current_product_name()

    return f"""🔥 {name}

最近正在找實用好物嗎？

這款 {name}
適合放進日常生活使用。

✨ 商品特色
✓ 簡單實用
✓ 日常方便
✓ 商品資訊清楚

🛒 想了解更多
可以到賣場看看！

#好物推薦 #蝦皮購物 #生活好物
"""


def local_tiktok_script():

    name = current_product_name()

    return f"""【0-3秒】
畫面快速帶出 {name}
字幕：
「最近很多人都在找這個！」

【3-7秒】
商品近距離展示。
鏡頭慢慢推近。

字幕：
「{name}」

【7-12秒】
展示商品外觀、包裝與細節。

字幕：
「實際商品以圖片為準」

【12-16秒】
展示商品使用情境。

字幕：
「日常生活好物」

【16-20秒】
商品主視覺＋行動呼籲。

字幕：
「想了解更多，前往賣場看看！」

影片比例：
9:16

影片風格：
乾淨、自然、商業廣告感。
"""


def local_jimeng():

    name = current_product_name()

    return f"""【即夢 AI 2.5 商品影片 Prompt】

9:16 vertical premium commercial product video.

Main product:
{name}

IMPORTANT PRODUCT PRESERVATION RULES:

Use the uploaded product image as the ONLY visual source
for the actual product appearance.

Preserve exactly:

- original product shape
- original packaging
- original colors
- original materials
- original logo
- original label
- original visible text
- original proportions
- original product structure

Do NOT:

- redesign the product
- change packaging
- invent logo
- invent brand
- invent product text
- modify label
- change product color
- change product shape
- create a different product

Camera:

slow cinematic push-in,
subtle orbit movement,
gentle close-up,
premium commercial photography.

Lighting:

soft studio lighting,
realistic reflections,
clean premium atmosphere.

Background:

minimal,
clean,
luxury commercial background.

Movement:

slow and stable,
no shaking,
no sudden camera movement.

Final frame:

clear hero shot of the original product.

Format:
9:16 vertical.
"""


# ============================================================
# AI 商品分析
# ============================================================

def run_product_analysis():

    name = current_product_name()

    category = st.session_state.category
    price = st.session_state.price
    stock = st.session_state.stock
    points = st.session_state.selling_points

    image_parts = []

    for image_file in st.session_state.images[:MAX_IMAGES]:

        part = image_to_part(image_file)

        if part:
            image_parts.append(part)

    prompt = f"""
你現在是「AI 蝦皮商品分析智能體」。

請分析使用者提供的商品資料與商品圖片。

商品名稱：
{name}

商品分類：
{category}

價格：
NT${price}

庫存：
{stock}

使用者提供的賣點：
{points}

非常重要：

商品圖片中的商品外觀是唯一可信的商品視覺來源。

禁止自行虛構：

- 品牌
- Logo
- 包裝
- 規格
- 容量
- 顏色
- 成分
- 功效
- 認證
- 商品文字

如果圖片看不到某項資料，
請明確寫「圖片未確認」。

請輸出：

1. 商品整體分析
2. 商品可見外觀
3. 商品可能的銷售重點
4. 不應虛構的資訊
5. 蝦皮標題建議
6. 商品描述
7. 關鍵字
8. 商品賣點
9. TikTok 文案
10. TikTok 20 秒腳本
11. 即夢 AI 2.5 Prompt

TikTok 必須使用 9:16。

即夢 Prompt 必須要求：
使用原始商品圖片作為商品唯一視覺來源，
保持商品原貌，不改 Logo、不改包裝、不改文字。

請使用繁體中文。
"""

    contents = [
        {
            "parts": [
                {
                    "text": prompt
                }
            ]
        }
    ]

    # 如果有圖片，附加到同一個 content
    if image_parts:

        contents[0]["parts"].extend(
            image_parts
        )

    result = gemini_request(contents)

    if result.get("ok"):

        st.session_state.analysis = result["text"]

        # 如果 Gemini 有成功，就保留原始 AI 結果
        # 同時建立其他欄位的安全預設
        st.session_state.title = local_title()
        st.session_state.description = local_description()
        st.session_state.keywords = local_keywords()
        st.session_state.selling_point_result = (
            st.session_state.selling_points
            or "請依實際商品圖片確認商品賣點。"
        )
        st.session_state.tiktok = local_tiktok()
        st.session_state.tiktok_script = local_tiktok_script()
        st.session_state.jimeng = local_jimeng()

        st.session_state.generated = True

        return True, "Gemini 分析完成"

    else:

        return False, result.get(
            "error",
            "Gemini 分析失敗"
        )


# ============================================================
# 產生內容
# ============================================================

def generate_all_content():

    name = current_product_name()

    # --------------------------------------------------------
    # 如果有 Gemini，使用 Gemini
    # --------------------------------------------------------

    if get_api_key():

        prompt = f"""
你是專業的台灣蝦皮電商 AI。

商品名稱：
{name}

商品分類：
{st.session_state.category}

價格：
NT${st.session_state.price}

庫存：
{st.session_state.stock}

商品狀態：
{st.session_state.condition}

使用者賣點：
{st.session_state.selling_points}

請根據商品圖片與以上資料，
產生以下內容：

【A 商品標題】
適合蝦皮搜尋與商品展示。

【B 商品描述】
繁體中文。

【C 關鍵字】
用逗號分隔。

【D 商品賣點】
列出 5 點。

【E TikTok 文案】
適合短影音。

【F TikTok 20 秒腳本】
9:16。

【G 即夢 AI 2.5 Prompt】
要求：
1. 商品圖片為唯一商品視覺來源。
2. 保持商品原始外觀。
3. 不修改 Logo。
4. 不修改包裝。
5. 不修改商品文字。
6. 不改變商品顏色。
7. 不改變商品形狀。
8. 不虛構品牌。

請使用以下格式：

[A]
...

[B]
...

[C]
...

[D]
...

[E]
...

[F]
...

[G]
...
"""

        image_parts = []

        for image_file in st.session_state.images[:MAX_IMAGES]:

            part = image_to_part(image_file)

            if part:
                image_parts.append(part)

        contents = [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]

        contents[0]["parts"].extend(
            image_parts
        )

        result = gemini_request(contents)

        if result.get("ok"):

            text = result["text"]

            st.session_state.analysis = text

            st.session_state.title = extract_section(
                text,
                "[A]",
                "[B]"
            ) or local_title()

            st.session_state.description = extract_section(
                text,
                "[B]",
                "[C]"
            ) or local_description()

            st.session_state.keywords = extract_section(
                text,
                "[C]",
                "[D]"
            ) or local_keywords()

            st.session_state.selling_point_result = extract_section(
                text,
                "[D]",
                "[E]"
            ) or st.session_state.selling_points

            st.session_state.tiktok = extract_section(
                text,
                "[E]",
                "[F]"
            ) or local_tiktok()

            st.session_state.tiktok_script = extract_section(
                text,
                "[F]",
                "[G]"
            ) or local_tiktok_script()

            st.session_state.jimeng = extract_section(
                text,
                "[G]",
                None
            ) or local_jimeng()

            st.session_state.generated = True

            return True, "Gemini 已完成 AI 商品內容生成"

        # API 失敗時，不讓 App 黑屏
        # 自動切換本地模式

        st.session_state.title = local_title()
        st.session_state.description = local_description()
        st.session_state.keywords = local_keywords()
        st.session_state.selling_point_result = (
            st.session_state.selling_points
            or "請依實際商品資訊確認。"
        )
        st.session_state.tiktok = local_tiktok()
        st.session_state.tiktok_script = local_tiktok_script()
        st.session_state.jimeng = local_jimeng()
        st.session_state.generated = True

        return False, (
            "Gemini API 暫時無法使用，"
            "已自動使用離線內容生成。"
            "\n\n"
            + result.get("error", "")
        )

    # --------------------------------------------------------
    # 無 API Key
    # --------------------------------------------------------

    st.session_state.analysis = (
        "目前未設定 Gemini API Key。\n\n"
        "系統已切換至離線展示模式。"
    )

    st.session_state.title = local_title()
    st.session_state.description = local_description()
    st.session_state.keywords = local_keywords()
    st.session_state.selling_point_result = (
        st.session_state.selling_points
        or "請依實際商品資訊確認。"
    )
    st.session_state.tiktok = local_tiktok()
    st.session_state.tiktok_script = local_tiktok_script()
    st.session_state.jimeng = local_jimeng()
    st.session_state.generated = True

    return False, "沒有 Gemini API Key，已使用離線模式"


# ============================================================
# 解析 Gemini 區塊
# ============================================================

def extract_section(text, start, end):

    if not text:
        return ""

    try:

        start_index = text.find(start)

        if start_index == -1:
            return ""

        start_index += len(start)

        if end:

            end_index = text.find(
                end,
                start_index
            )

            if end_index == -1:
               
