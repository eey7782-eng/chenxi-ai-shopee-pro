import streamlit as st
import requests
import json
import base64

st.set_page_config(page_title="蝦皮獨家爆款 AI 戰術系統", page_icon="🔥", layout="wide")

api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.title("🔑 API 設定")
    api_key = st.text_input("請貼上您的 Gemini API Key：", type="password")

if api_key:
    st.title("🔥 蝦皮獨家爆款 AI 戰術系統 (您的專屬 Prompt 影片引擎)")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        product_name = st.text_input("商品名稱", "Acens 精華液")
        category = st.selectbox(
            "商品分類",
            ["美妝保養 / 個人護理", "3C 數碼 / 電腦周邊", "手機配件 / 各類周邊", "女裝 / 包包與服飾", "居家生活", "美食零食", "其他"]
        )
        price = st.number_input("商品價格 (NT$)", value=499)
        competitor_flaw = st.text_input("競品常見痛點/缺點", "市售常見精華液太黏膩、吸收慢、容易起屑")
        selling_points = st.text_area("本品獨家賣點", "極速吸收、專利控油成分、敏弱肌專用")
        
        st.divider()
        st.subheader("🎬 您的專屬 9:16 AI 影片指令 (已自動套用)")
        
        # 將您的專屬 Prompt 作為動態模板
        default_user_prompt = (
            f"Use the product '{product_name}' ({selling_points}) as the only subject. "
            "Keep its original brand, packaging, colors, text, proportions, and details unchanged. "
            "Create a premium e-commerce visual with the product centered on a clean background. "
            "For posters, use Traditional Chinese titles and three selling points. "
            "For videos, use smooth full-view-to-close-up camera movement. "
            "No people, hands, watermarks, extra products, altered packaging, messy backgrounds, or exaggerated claims. "
            "Suitable for Shopee and TikTok. 9:16 vertical 4k studio lighting."
        )
        
        custom_video_prompt = st.text_area("已為您整合萬用指令：", default_user_prompt, height=180)
        
        uploaded_file = st.file_uploader("上傳商品圖片 (選填，有上傳會優先以原圖做 9:16 運鏡)", type=["jpg", "jpeg", "png"])
        
        btn = st.button("🚀 生成戰術行銷包 + 專屬指令 9:16 影片", type="primary", use_container_width=True)

    with col2:
        if btn:
            # 1. 生成行銷文案與腳本
            with st.spinner("AI 正在分析競品痛點並生成文案..."):
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
                    
                    prompt = f"""你是一位頂級電商行銷操盤手。針對以下商品：
- 名稱：{product_name}
- 分類：{category}
- 價格：NT$ {price}
- 競品痛點：{competitor_flaw}
- 本品賣點：{selling_points}

請依據繁體中文輸出：
1. 🥊 高轉化蝦皮標題 (60字內)
2. 🎯 五感沉浸式商品描述 (含競品避坑指南、痛點解決、3大賣點)
3. 📈 蝦皮搜尋演算法關鍵字矩陣
4. 🎬 TikTok / Shopee 9:16 衝動購物型短影音分鏡腳本
"""
                    parts = [{"text": prompt}]
                    
                    if uploaded_file:
                        bytes_data = uploaded_file.getvalue()
                        base64_img = base64.b64encode(bytes_data).decode("utf-8")
                        parts.append({
                            "inline_data": {
                                "mime_type": uploaded_file.type,
                                "data": base64_img
                            }
                        })
                        
                    payload = {"contents": [{"parts": parts}]}
                    res = requests.post(url, json=payload, timeout=90)
                    
                    if res.status_code == 200:
                        data = res.json()
                        result_text = data["candidates"][0]["content"]["parts"][0]["text"]
                        st.success("✨ 獨家戰術行銷包生成完成！")
                        st.code(result_text, language="markdown")
                    else:
                        st.error(f"API 錯誤：{res.text}")
                except Exception as e:
                    st.error(f"執行出錯：{str(e)}")

            # 2. 嚴格執行您的 Prompt 規範進行 9:16 動態運鏡與繪製
            st.divider()
            st.subheader("🎥 6. 依據您的指令生成的 9:16 展演短影音")
            
            if uploaded_file:
                img_data = base64.b64encode(uploaded_file.getvalue()).decode()
                img_src = f"data:{uploaded_file.type};base64,{img_data}"
            else:
                img_src = f"https://pollinations.ai/p/{custom_video_prompt.replace(' ', '%20')}?width=720&height=1280&seed=42&model=flux"

            html_code = f"""
            <div style="display: flex; flex-direction: column; align-items: center; gap: 15px;">
                <!-- 9:16 Canvas (360x640) 無浮水印、純淨背景、相容 TikTok/蝦皮安全區 -->
                <canvas id="shopeeCanvas" width="360" height="640" style="border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); background: #111;"></canvas>
                <div style="display: flex; gap: 10px;">
                    <button id="recBtn" onclick="startRecording()" style="padding: 10px 20px; background: #FF5722; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">🎥 渲染 9:16 全景至特寫運鏡影片</button>
                    <a id="downloadLink" style="display: none; padding: 10px 20px; background: #00C853; color: white; border-radius: 8px; font-weight: bold; text-decoration: none;">📥 下載蝦皮/TikTok 相容 MP4 (.mp4)</a>
                </div>
            </div>

            <script>
                const canvas = document.getElementById('shopeeCanvas');
                const ctx = canvas.getContext('2d');
                const img = new Image();
                img.crossOrigin = "Anonymous";
                img.src = "{img_src}";

                let scale = 1.0;
                let step = 0;

                img.onload = function() {{
                    drawFrame();
                }};

                function drawFrame() {{
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    
                    // 保持原圖片比例與細節，置於純淨背景中
                    const imgRatio = img.width / img.height;
                    const canvasRatio = canvas.width / canvas.height;
                    let renderW, renderH;

                    if (imgRatio > canvasRatio) {{
                        renderH = canvas.height * 0.70;
                        renderW = renderH * imgRatio;
                    }} else {{
                        renderW = canvas.width * 0.80;
                        renderH = renderW / imgRatio;
                    }}

                    // 執行您的指令規範：從「全景平滑推進至特寫 (smooth full-view-to-close-up camera movement)」
                    // 使用正弦曲線模擬專業攝影滑軌
                    const progress = (Math.sin(step * 0.015) + 1) / 2; // 0 到 1 循環
                    scale = 1.0 + progress * 0.22; // 由 1.0 倍推近至 1.22 倍特寫

                    const finalW = renderW * scale;
                    const finalH = renderH * scale;
                    
                    const offsetX = (canvas.width - finalW) / 2;
                    const offsetY = (canvas.height - finalH) / 2 - 20;

                    // 極簡高品質工作室純色背景 (Clean background, no messy background)
                    ctx.fillStyle = "#121212";
                    ctx.fillRect(0, 0, canvas.width, canvas.height);
                    
                    // 渲染商品本體 (保持比例不變形)
                    ctx.drawImage(img, offsetX, offsetY, finalW, finalH);

                    // 柔和專業棚燈光影 (Studio Lighting)
                    const gradient = ctx.createRadialGradient(
                        canvas.width/2, canvas.height/2 - 20, 50,
                        canvas.width/2, canvas.height/2 - 20, 250
                    );
                    gradient.addColorStop(0, 'rgba(255,255,255,0.08)');
                    gradient.addColorStop(1, 'rgba(0,0,0,0.5)');
                    ctx.fillStyle = gradient;
                    ctx.fillRect(0, 0, canvas.width, canvas.height);

                    // 繁體中文 3 大賣點安全區資訊卡 (避開邊界與 UI 遮擋)
                    const boxW = canvas.width - 50;
                    const boxH = 55;
                    const boxX = 25;
                    const boxY = canvas.height - 115;

                    ctx.fillStyle = "rgba(0,0,0,0.8)";
                    ctx.roundRect(boxX, boxY, boxW, boxH, 10);
                    ctx.fill();

                    ctx.fillStyle = "#FFFFFF";
                    ctx.font = "bold 13px -apple-system, BlinkMacSystemFont, sans-serif";
                    const displayTitle = "{product_name}".length > 14 ? "{product_name}".substring(0, 14) + "..." : "{product_name}";
                    ctx.fillText(displayTitle, boxX + 12, boxY + 22);

                    ctx.fillStyle = "#FF5722";
                    ctx.font = "bold 11px sans-serif";
                    const spText = "{selling_points}".replace(/\\n/g, ' | ').substring(0, 22);
                    ctx.fillText("✨ " + spText, boxX + 12, boxY + 41);

                    step++;
                    requestAnimationFrame(drawFrame);
                }}

                function startRecording() {{
                    const btn = document.getElementById('recBtn');
                    btn.innerText = "⏳ 正在依照您的指令運算 9:16 影片...";
                    btn.disabled = true;

                    let options = {{ mimeType: 'video/mp4;codecs=avc1.42E01E' }};
                    if (!MediaRecorder.isTypeSupported(options.mimeType)) {{
                        options = {{ mimeType: 'video/mp4' }};
                    }}
                    if (!MediaRecorder.isTypeSupported(options.mimeType)) {{
                        options = {{ mimeType: 'video/webm;codecs=h264' }};
                    }}

                    const stream = canvas.captureStream(30);
                    const mediaRecorder = new MediaRecorder(stream, options);
                    let chunks = [];

                    mediaRecorder.ondataavailable = e => chunks.push(e.data);
                    mediaRecorder.onstop = e => {{
                        const blob = new Blob(chunks, {{ type: 'video/mp4' }});
                        const url = URL.createObjectURL(blob);
                        const a = document.getElementById('downloadLink');
                        a.href = url;
                        a.download = "{product_name}_CustomPrompt_9x16.mp4";
                        a.style.display = "inline-block";
                        btn.innerText = "✅ 渲染完成！";
                    }};

                    mediaRecorder.start();
                    setTimeout(() => mediaRecorder.stop(), 15000);
                }}
            </script>
            """
            st.components.v1.html(html_code, height=720)
