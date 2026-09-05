import time
from openai import OpenAI
from playwright.sync_api import sync_playwright

# 初始化 OpenAI Client
client = OpenAI(api_key="你的_OPENAI_API_KEY")

def generate_video_prompt(product_description: str) -> str:
    """讓 OpenAI 生成帶有鏡頭運鏡與動態描述的影片提示詞"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一位專業的電商短影音導演。請根據商品描述，生成一段適合 AI 影片工具（如即夢 AI、Sora、Luma）"
                    "使用的英文 Video Prompt。必須包含：光影變化、背景動態、鏡頭運鏡描述（例如 slow panning, "
                    "soft light flickering, 4k resolution, cinematic commercial film）。只需回傳英文 Prompt。"
                )
            },
            {
                "role": "user",
                "content": f"商品描述：{product_description}"
            }
        ]
    )
    prompt = response.choices[0].message.content.strip()
    print(f"🎬 1. OpenAI 已生成影片提示詞：\n{prompt}\n")
    return prompt

def run_jimeng_video_automation(prompt_text: str):
    """使用 Playwright 操作即夢 AI 網頁生成短影片"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("🌐 2. 開啟即夢 AI 官網...")
        page.goto("https://jimeng.jianying.com/")
        
        print("⏳ 請確認完成即夢帳號登入...")
        page.wait_for_selector("textarea", timeout=60000)

        # 點擊切換至「影片生成/視頻生成」分頁
        video_tab = page.query_selector("text='視頻生成'") or page.query_selector("text='視頻'") or page.query_selector("text='影片'")
        if video_tab:
            video_tab.click()
            print("🎥 3. 已切換至『影片生成』模式")
            time.sleep(2)

        # 填入影片提示詞
        prompt_input = page.query_selector("textarea")
        if prompt_input:
            prompt_input.fill(prompt_text)
            print("✅ 4. 已自動輸入影片提示詞！")

        # 自動點擊生成按鈕
        generate_btn = page.query_selector("button:has-text('生成')")
        if generate_btn:
            generate_btn.click()
            print("🚀 5. 已觸發影片生成！(影片算圖通常需要 1~3 分鐘，請稍候)")

        # 影片生成時間較長，設定等待時間
        time.sleep(60)
        browser.close()

if __name__ == "__main__":
    my_product = "香水瓶放在清澈水面上，水波漣漪，陽光穿透水滴，慢動作鏡頭特寫"
    
    # 步驟 1: 生成影片提示詞
    video_prompt = generate_video_prompt(my_product)
    
    # 步驟 2: 自動化生成影片
    run_jimeng_video_automation(video_prompt)
