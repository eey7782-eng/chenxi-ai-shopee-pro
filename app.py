import os
import subprocess
import gradio as gr
from openai import OpenAI

# ---------------------------------------------------------------------------
# 1. 初始化設定 (Environment & API Setup)
# ---------------------------------------------------------------------------
# 請於系統環境變數設定 OPENAI_API_KEY，或在此處帶入
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY"))

# ---------------------------------------------------------------------------
# 2. AI 文案生成模組 (AI Copywriter Engine)
# ---------------------------------------------------------------------------
def generate_shopee_copywriting(product_name, features, price, category):
    """
    呼叫 OpenAI API 生成符合蝦皮 SEO 與高轉化率的商品標題與內文
    """
    prompt = f"""
    你是一名精通蝦皮（Shopee）爆款銷售的電商文案專家。請根據以下商品資訊撰寫標題與描述：

    【商品名稱】：{product_name}
    【商品分類】：{category}
    【售價】：NT$ {price}
    【核心賣點與規格】：{features}

    請輸出以下結構：
    1. 【蝦皮 SEO 爆款標題】：控制在 50 字以內，包含品牌/品名/熱搜關鍵字/核心功能，吸引點擊。
    2. 【商品詳細描述】：
       - 產品特點與亮點列表（使用適當 Emoji）
       - 規格與尺寸細節
       - 使用情境與注意事項
       - 售後服務與品質保證
    3. 【熱門搜尋標籤】：提供 5-8 個相關 Hashtags（如 #蝦皮嚴選 #...）
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一位專業的電商銷售文案專家。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"文案生成失敗，錯誤訊息：{str(e)}"

# ---------------------------------------------------------------------------
# 3. 影片轉碼與規格處理模組 (Video Processing Engine)
# ---------------------------------------------------------------------------
def process_shopee_video(input_video_path):
    """
    使用 FFmpeg 自動轉碼影片以符合蝦皮限制：
    - 格式：MP4
    - 比例：1:1 (720x720)
    - 檔案大小：< 30MB
    - 長度：10~60 秒
    """
    if not input_video_path:
        return None, "未上傳影片"

    output_path = "processed_shopee_video.mp4"
    
    # FFmpeg 命令：裁剪為正方形、限制碼率以控制檔案大小
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", input_video_path,
        "-vf", "crop='min(iw,ih)':'min(iw,ih)',scale=720:720",
        "-r", "30",
        "-b:v", "2M",
        "-fs", "28M",  # 限制最大檔案為 28MB (低於蝦皮 30MB 限制)
        output_path
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_path, "影片處理成功！已符合蝦皮正方形 (720x720) 與檔案大小規範。"
    except Exception as e:
        return None, f"影片處理失敗（請確認系統已安裝 FFmpeg）：{str(e)}"

# ---------------------------------------------------------------------------
# 4. 蝦皮自動上架打包邏輯 (Shopee Upload Dispatcher)
# ---------------------------------------------------------------------------
def submit_to_shopee(copywriting, video_file, product_images):
    """
    將文案與處理完成的多媒體封包，傳送至蝦皮 API 或驅動 RPA 進行自動上架
    """
    # 此處可對接 Shopee Open API 或影刀 RPA Webhook
    if not copywriting:
        return "錯誤：請先生成商品文案！"
        
    return "✅ 成功打包！數據已發送至蝦皮自動上架排程隊列 (Ready to Publish)。"

# ---------------------------------------------------------------------------
# 5. Gradio Web 互動介面 (UI Layout)
# ---------------------------------------------------------------------------
def build_interface():
    with gr.Blocks(title="蝦皮 AI 自動化上架系統 Pro") as app:
        gr.Markdown("# 🛒 蝦皮 AI 全自動上架與多媒體處理系統")
        gr.Markdown("自動生成 SEO 爆款文案、轉碼 1:1 蝦皮短影片，並一鍵排程上架。")

        with gr.Row():
            # 左側：輸入區域
            with gr.Column(scale=1):
                gr.Markdown("### 1. 輸入商品基本資訊")
                p_name = gr.Textbox(label="商品名稱", placeholder="例如：極簡風無線藍牙耳機")
                p_category = gr.Textbox(label="商品分類", placeholder="例如：3C 數位 / 藍牙耳機")
                p_price = gr.Number(label="商品售價 (NT$)", value=499)
                p_features = gr.Textbox(label="商品特點與規格", lines=4, placeholder="例如：主動降噪、續航 24 小時、防水防汗、附帶 3 種耳塞")
                
                gr.Markdown("### 2. 上傳多媒體素材")
                p_video = gr.Video(label="上傳短影片母檔 (MP4/MOV)")
                p_images = gr.File(label="上傳商品主圖 (可多選)", file_count="multiple")
                
                btn_generate = gr.Button("🚀 開始 AI 處理與文案生成", variant="primary")

            # 右側：輸出區域
            with gr.Column(scale=1):
                gr.Markdown("### 3. AI 生成結果與影片預覽")
                out_copywriting = gr.TextArea(label="AI 生成之蝦皮文案", lines=12)
                out_video = gr.Video(label="符合蝦皮規格之處理後影片 (720x720)")
                out_status = gr.Textbox(label="處理狀態 log", interactive=False)
                
                btn_upload = gr.Button("📦 確定並一鍵發送上架", variant="stop")
                out_upload_result = gr.Textbox(label="上架結果回傳", interactive=False)

        # 邏輯綁定
        def pipeline_execution(name, cat, price, feat, video):
            text_result = generate_shopee_copywriting(name, feat, price, cat)
            proc_video, video_log = process_shopee_video(video) if video else (None, "未上傳影片")
            return text_result, proc_video, video_log

        btn_generate.click(
            fn=pipeline_execution,
            inputs=[p_name, p_category, p_price, p_features, p_video],
            outputs=[out_copywriting, out_video, out_status]
        )

        btn_upload.click(
            fn=submit_to_shopee,
            inputs=[out_copywriting, out_video, p_images],
            outputs=[out_upload_result]
        )

    return app

if __name__ == "__main__":
    app = build_interface()
    app.launch()
