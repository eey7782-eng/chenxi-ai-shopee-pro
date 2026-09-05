import io
import time
import urllib.parse
import zipfile
import requests
from enum import Enum
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from PIL import Image, ImageEnhance, ImageFilter
from rembg import remove
from google import genai
from google.genai import types
import uvicorn

# ==========================================
# 🔑 金鑰設定區 (請在此處填入你的 API Key)
# ==========================================
GEMINI_API_KEY = "你的_GEMINI_API_KEY"
SILICONFLOW_API_KEY = "你的_SILICONFLOW_API_KEY"

# 初始化 Gemini Client (使用最新 google-genai SDK)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI(
    title="多平台電商 AI 自動化 API 服務",
    description="整合 Gemini 邏輯分析與 SiliconFlow 生成模型，提供白底去背、AI 海報與短影音生成服務",
    version="2.0.0"
)

class PlatformEnum(str, Enum):
    coupang = "coupang"
    momo = "momo"
    shopee = "shopee"

class ECommerceService:
    @staticmethod
    def enhance_product(img: Image.Image) -> Image.Image:
        """提升商品邊緣銳利度"""
        enhancer = ImageEnhance.Sharpness(img)
        return enhancer.enhance(1.2)

    @staticmethod
    def generate_shadow(fg_mask: Image.Image, blur_radius=15, opacity=85) -> Image.Image:
        """產生自然接觸陰影"""
        shadow = fg_mask.split()[-1].filter(ImageFilter.GaussianBlur(blur_radius))
        shadow_img = Image.new("RGBA", fg_mask.size, (0, 0, 0, 0))
        shadow_img.putalpha(shadow)
        alpha = shadow_img.split()[-1]
        alpha = alpha.point(lambda p: int(p * (opacity / 255.0)))
        shadow_img.putalpha(alpha)
        return shadow_img

    @classmethod
    def build_white_bg(cls, fg_img: Image.Image, canvas_size=(1000, 1000)) -> Image.Image:
        """酷澎 / momo 專用：1000x1000 純白底 (80% 商品占比居中)"""
        canvas = Image.new("RGBA", canvas_size, (255, 255, 255, 255))
        max_dim = int(canvas_size[0] * 0.8)
        fg_copy = fg_img.copy()
        fg_copy.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        x = (canvas_size[0] - fg_copy.width) // 2
        y = (canvas_size[1] - fg_copy.height) // 2
        canvas.paste(fg_copy, (x, y), mask=fg_copy)
        return canvas.convert("RGB")

    @classmethod
    def generate_siliconflow_bg(cls, prompt: str, canvas_size=(1024, 1024)) -> Image.Image:
        """使用 SiliconFlow (FLUX.1) 生成高質感 AI 背景圖"""
        url = "https://api.siliconflow.cn/v1/image/generations"
        headers = {
            "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "black-forest-labs/FLUX.1-schnell",
            "prompt": f"empty background, empty studio table, {prompt}, soft studio lighting, highly detailed, photorealistic, no objects in center",
            "width": canvas_size[0],
            "height": canvas_size[1]
        }
        
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=30)
            data = res.json()
            image_url = data["images"][0]["url"]
            img_res = requests.get(image_url, timeout=20)
            return Image.open(io.BytesIO(img_res.content)).convert("RGBA")
        except Exception as e:
            # 備用機制：若 API 異常則使用 Pollinations 免費繪圖
            encoded_prompt = urllib.parse.quote(prompt)
            fallback_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={canvas_size[0]}&height={canvas_size[1]}&model=flux&nologo=true"
            bg_res = requests.get(fallback_url, timeout=20)
            return Image.open(io.BytesIO(bg_res.content)).convert("RGBA")

    @classmethod
    def build_shopee_ai_bg(cls, fg_img: Image.Image, prompt: str, canvas_size=(1024, 1024)) -> Image.Image:
        """蝦皮專用：AI 背景 + 自動陰影疊加合成"""
        bg = cls.generate_siliconflow_bg(prompt, canvas_size)
        max_dim = int(canvas_size[0] * 0.7)
        fg_copy = fg_img.copy()
        fg_copy.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        shadow = cls.generate_shadow(fg_copy, blur_radius=20, opacity=85)
        x = (canvas_size[0] - fg_copy.width) // 2
        y = (canvas_size[1] - fg_copy.height) // 2

        bg.paste(shadow, (x, y + 10), mask=shadow)
        bg.paste(fg_copy, (x, y), mask=fg_copy)
        return bg.convert("RGB")

    @classmethod
    def analyze_image_and_get_prompt(cls, img_bytes: bytes) -> str:
        """呼叫 Gemini Vision API 分析商品，並自動生成最適合的背景 Prompt"""
        try:
            image = Image.open(io.BytesIO(img_bytes))
            prompt_text = "Analyze this product image. Output a 1-sentence English prompt for generating a matching background scene for e-commerce, such as table material and lighting. Only output the English prompt."
            
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[image, prompt_text]
            )
            return response.text.strip()
        except Exception:
            return "modern wooden table, soft warm studio sunlight, blurred background"

# --- API 端點 ---

@app.post("/api/v1/process-image", summary="單張商品圖處理")
async def process_image(
    file: UploadFile = File(..., description="商品照片 (JPG/PNG)"),
    platform: PlatformEnum = Form(..., description="上架平台 (coupang / momo / shopee)"),
    custom_prompt: Optional[str] = Form(None, description="可選：自訂蝦皮背景描述 (留空將由 Gemini 自動分析生成)")
):
    contents = await file.read()
    raw_img = Image.open(io.BytesIO(contents)).convert("RGBA")
    nobg_img = remove(raw_img)
    nobg_img = ECommerceService.enhance_product(nobg_img)

    if platform in [PlatformEnum.coupang, PlatformEnum.momo]:
        result_img = ECommerceService.build_white_bg(nobg_img)
    elif platform == PlatformEnum.shopee:
        # 若未指定 prompt，則由 Gemini 自動辨識商品並產生
        prompt = custom_prompt or ECommerceService.analyze_image_and_get_prompt(contents)
        result_img = ECommerceService.build_shopee_ai_bg(nobg_img, prompt)

    output_buffer = io.BytesIO()
    result_img.save(output_buffer, format="JPEG", quality=95)
    
    return Response(
        content=output_buffer.getvalue(),
        media_type="image/jpeg",
        headers={"Content-Disposition": f"inline; filename={platform.value}_output.jpg"}
    )

@app.post("/api/v1/process-batch-zip", summary="批次處理圖片並回傳 ZIP 壓縮檔")
async def process_batch_zip(
    files: List[UploadFile] = File(..., description="上傳多張圖片"),
    platform: PlatformEnum = Form(..., description="目標平台")
):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for idx, file in enumerate(files):
            if not file.content_type.startswith("image/"):
                continue
            try:
                contents = await file.read()
                raw_img = Image.open(io.BytesIO(contents)).convert("RGBA")
                nobg_img = remove(raw_img)
                nobg_img = ECommerceService.enhance_product(nobg_img)

                if platform in [PlatformEnum.coupang, PlatformEnum.momo]:
                    res_img = ECommerceService.build_white_bg(nobg_img)
                else:
                    prompt = ECommerceService.analyze_image_and_get_prompt(contents)
                    res_img = ECommerceService.build_shopee_ai_bg(nobg_img, prompt)

                out_buf = io.BytesIO()
                res_img.save(out_buf, format="JPEG", quality=95)
                
                orig_name = file.filename.split(".")[0] if file.filename else f"product_{idx+1}"
                zip_file.writestr(f"{platform.value}_{orig_name}.jpg", out_buf.getvalue())
            except Exception as e:
                zip_file.writestr(f"ERROR_{file.filename}.txt", str(e))

    zip_buffer.seek(0)
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={platform.value}_batch.zip"}
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
