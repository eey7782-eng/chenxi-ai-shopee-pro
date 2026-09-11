# app.py - 2026 龍蝦系統 / 黑金剛系列 V500 PRO 4.0 整合後端
import streamlit as st

# 1. 頁面基本設定
st.set_page_config(
    page_title="2026 龍蝦系統 / V500 PRO 4.0 帶貨提示詞產生器",
    page_icon="🦞",
    layout="wide"
)

# 2. V500 PRO 4.0 與龍蝦系統全系列提示詞資料庫
PROMPT_DATABASE = {
    # ── 核心旗艦協議 ──
    "龍蝦 15.0 幽靈避險協議 (Supreme V5)": {
        "engine": "全平台通用旗艦",
        "code": """[PROTOCOL: SUPREME_V5]
CORE: @Image1 (Creator) + @Image2 (Product). 9:16.
[PHYSICS]: High-pressure grip, 20% finger indentation, shoulder tension, natural weight shift, 360-rotation.
[OPTICS]: Rack-focus eyes to label, f/1.8, organic lens breathing, 8k raw skin pores, messy hair, fabric lint.
[CLARITY]: Force hyper-clear/readable logos/labels, no warping.
[SYNC]: Elastic mouth, throat muscle movement, chest breathing, natural blinking behavior.
[BYPASS]: 20% film grain, handheld shaky (intensity 1.5), lens flares, chromatic aberration.
[OUTPUT]: Raw Cine-Photo, no CGI."""
    },
    "OMNI-SHIELD V7 終極縮減協議": {
        "engine": "極致防護核心",
        "code": """[PROMPT]: 8k raw, @Image1 x @Image2. 9:16.
[BIO]: CapillaryReaction(pale-to-pink), SkinIndentation:35%, Physical pores, Organic skin fuzz.
[LIGHT]: Tiangong Aesthetic Flow, LightRefraction, 15% film grain, HandheldShake:1.2Hz, Dynamic bokeh.
[SYNC]: High-fidelity facial muscle tension, Exaggerated labial movement, Deep muscular lip-sync ready.
[BEYOND]: No VFX, InvisibleMetadataMask, Bypass 2026 Detection, Total Organic Realism."""
    },
    
    # ── 跨平台專用引擎 ──
    "黑金剛 V4.0 (即夢 / 剪映專用)": {
        "engine": "即夢 Jimeng 2.0",
        "code": "[PROTOCOL: BLACK_KONG_V4] Professional creator, identical to 【@Image1】, holding and presenting product 【@Image2】. [Logic]: 8k raw cine-photo, messy hair, physical pores. [Anti-Detection]: 15% film grain, handheld shake, bypass 2026 detection. [Sync Ready]: Exaggerated mouth shapes for perfect AI lip-sync. No VFX, cinematic realism. 9:16."
    },
    "Skywork 天工專用協議 (物理旋轉)": {
        "engine": "Skywork 天工",
        "code": "[PROTOCOL: SKY_WORK_SHIELD] A real-life professional creator, consistent with the reference person, is sitting at a desk and physically picking up and rotating the product from 【@Image2】. [Strategy: Anti-AI]: Cinematic 8k, raw texture, visible skin pores, slightly messy hair, 15% realistic film grain. [Strategy: Motion]: Natural handheld camera micro-shaking, organic lens breathing. Vertical 9:16, no CGI effects."
    },
    "Kling 可靈專用協議 (物理吞嚥/食品)": {
        "engine": "Kling 可靈",
        "code": "[PROTOCOL: KLING_PHYSICS_PLUS] Close-up interaction, creator 【@Image1】 holding product 【@Image2】 with high-pressure grip, 15% finger indentation, realistic weight shift. 8k raw cine-photo, messy hair, organic skin texture. Camera: handheld micro-shaking, rack-focus to product labels. Bypass 2026 AI detection, no CGI, vertical 9:16."
    },
    "TikTok 專用黑金剛 4.0 流量爆發版": {
        "engine": "TikTok 專用",
        "code": "[PROTOCOL: TIKTOK_KING_BYPASS] Professional creator as 【@Image1】 enthusiastically presenting product 【@Image2】 with a dynamic visual hook in the first 3 seconds. [Logic]: 8k raw cine-photo, messy hair, skin pores, 100% human authenticity. [Anti-Detection]: 20% digital film grain, handheld camera shake, organic lens flares to bypass TikTok 2026 AI labeling. [Sync Ready]: High-fidelity lip-sync for real voiceover. Vertical 9:16, masterpiece. No VFX."
    },

    # ── V500 PRO 4.0 模組清單對應 ──
    "01 真人商品展示": "Real-life creator presenting product, 8k raw cine-photo, natural skin texture, vertical 9:16.",
    "03 食品開箱展示": "Close-up food unboxing interaction, high-pressure grip, 15% finger indentation, organic texture, vertical 9:16.",
    "07 服飾展示": "Advanced fabric simulation, natural wrinkles and folds, visible weight distribution, vertical 9:16.",
    "11 TikTok商品口播": "Dynamic creator talking to camera, sync-ready mouth shapes, handheld shaky, fast-paced vertical 9:16.",
    "16 蝦皮商品主圖": "E-commerce product main image, hyper-clear labels, clean commercial lighting, 8k detail.",
    "21 黑金風商品展示": "Dark luxury style, gold accent lighting, high-end commercial aesthetic, 8k resolution.",
    "46 設計師辰曦專區": "Designer Chen Xi exclusive aesthetic, minimalist luxury, cinematic lighting, ultra-high detail."
}

# 3. 萬用負向提示詞
UNIVERSAL_NEGATIVE_PROMPT = (
    "watermark, logo, signature, text, low quality, blurry, duplicate, "
    "extra fingers, extra limbs, bad anatomy, distorted face, plastic skin, "
    "cartoon style, 3d render, oversaturated, low resolution, unrealistic lighting, "
    "floating objects, warped products"
)

# 4. Streamlit 介面設計
st.title("🦞 2026 龍蝦系統 / V500 PRO 4.0 終極提示詞產生器")
st.markdown("**系統版本：** V500 PRO 4.0 MASTER BACKUP | **建立人：** 設計師辰曦 | **系統狀態：** 正常運作 🚀")
st.markdown("---")

# 側邊欄與主要輸入區
with st.sidebar:
    st.header("⚙️ 系統參數設定")
    selected_module = st.selectbox("選擇核心協議 / 模組", list(PROMPT_DATABASE.keys()))
    
    st.markdown("---")
    img1_input = st.text_input("主播／人物參考標籤 (Image1)", "Creator_Model")
    img2_input = st.text_input("產品參考標籤 (Image2)", "Product_Item")
    
    st.markdown("### 📐 標準輸出規格")
    st.info("尺寸: 9:16 (1080x1920)\n風格: Photorealistic\n品質: Commercial Quality")

# 主畫面生成邏輯
col1, col2 = st.columns(2)

with col1:
    st.subheader("🎯 產出的正向提示詞 (Prompt)")
    
    if st.button("🚀 一鍵生成終極避險代碼", type="primary"):
        target_data = PROMPT_DATABASE[selected_module]
        
        # 判斷是字典結構還是純字串
        if isinstance(target_data, dict):
            base_code = target_data["code"]
            engine_name = target_data["engine"]
        else:
            base_code = target_data
            engine_name = "V500 模組化場景"
            
        # 變數替換
        final_prompt = base_code.replace("【@Image1】", f"@{img1_input}").replace("【@Image2】", f"@{img2_input}")
        final_prompt = final_prompt.replace("@Image1", f"@{img1_input}").replace("@Image2", f"@{img2_input}")
        
        # 附加包裝
        complete_output = f"[SYSTEM: V500_PRO_4.0] [ENGINE: {engine_name}]\n{final_prompt}\n[OUTPUT]: 9:16, 1080x1920, Photorealistic, No CGI."
        
        st.code(complete_output, language="text")
        st.success(f"✅ 成功載入 [{engine_name}] 協議！")
    else:
        st.info("請在左側輸入參數並點擊按鈕生成提示詞。")

with col2:
    st.subheader("🚫 萬用負向提示詞 (Negative Prompt)")
    st.code(UNIVERSAL_NEGATIVE_PROMPT, language="text")
    st.markdown("---")
    st.warning("💡 **提示：** 產出的代碼可直接複製並貼入即夢、天工、可靈或對應的 AI 影片生成平台。")
