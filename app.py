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
    st.title("🔥 蝦皮獨家爆款 AI 戰術系統 (自訂指令影片生成版)")
    
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
        st.subheader("🎬 自訂 9:16 影片視覺指令 (核心)")
        custom_video_prompt = st.text_area(
            "請輸入您的專屬影片指令（例如：luxury cosmetic bottle on marble stone, cinematic warm lighting, 4k, vertical）", 
            f"commercial product photography of {product_name}, luxury studio lighting, high resolution, 4k, vertical view"
        )
        
        uploaded_file = st.file_uploader("上傳商品圖片 (選填，若未上傳將依據上方指令自動繪製圖面)", type=["jpg", "jpeg", "png"])
        
        btn = st.button("🚀 執行 AI 文案 + 依照指令生成 9:16 影片", type="primary", use_container_width=True)

    with col2:
        if btn:
            # 1. 生成行銷文案與腳本
            with st.spinner("AI 正在分析並生成文案..."):
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
                    
                    prompt = f"""你是一位頂級電商行銷操盤手。針對以下商品：
- 名稱：{product_name}
- 分類：{category}
- 價格：NT$ {price}
- 競品痛點：{competitor_flaw}
- 本品賣點：{selling_points}

請輸出：
1. 🥊 高轉化蝦皮標題 (60字內)
2. 🎯 五感沉浸式商品描述
3. 📈 蝦皮搜尋演算法關鍵字矩陣
4. 🎬 短影音分鏡腳本
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
                        st.success("✨ 行銷戰術包生成完成！")
                        st.code(result_text, language="markdown")
                    else:
                        st.error(f"API 錯誤：{res.text}")
                except Exception as e:
                    st.error(f"執行出錯：{str(e)}")

            # 2. 嚴格依據使用者自訂指令渲染 9:16 影片
            st.divider()
            st.subheader("🎥 6. 依據您的指令所生成的 9:16 短影音")
            
            if uploaded_file:
                img_data = base64.b64encode(uploaded_file.getvalue()).decode()
                img_src = f"data:{uploaded_file.type};base64,{img_data}"
            else:
                # 這裡直接套用使用者在左側輸入的 custom_video_prompt 去繪製畫面
                img_src = f"https://pollinations.ai/p/{custom_video_prompt.replace(' ', '%20')}?width=720&height=1280&seed=42&model=flux"

            html_code = f"""
            <div style="display: flex; flex-direction: column; align-items: center; gap: 15px;">
                <!-- 9:16 Canvas (360x640) 完美防遮擋安全比例 -->
                <canvas id="shopeeCanvas" width="360" height="640" style="border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); background: #111;"></canvas>
                <div style="display: flex; gap: 10px;">
                    <button id="recBtn" onclick="startRecording()" style="padding: 10px 20px; background: #FF5722; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">🎥 開始依照指令渲染 9:16 影片</button>
                    <a id="downloadLink" style="display: none; padding: 10px 20px; background: #00C853; color: white; border-radius: 8px; font-weight: bold; text-decoration: none;">📥 下載您的自訂指令 9:16 MP4</a>
                </div>
            </div>

            <script>
                const canvas = document.getElementById('shopeeCanvas');
                const ctx = canvas.getContext('2d');
                const img = new Image();
                img.crossOrigin = "Anonymous";
                img.src = "{img_src}";

                let scale = 1.0;
                let lightX = -360;
                let step = 0;

                img.onload = function() {{
                    drawFrame();
                }};

                function drawFrame() {{
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    
                    // 等比例縮放與置中，防止畫面變形或過大
                    const imgRatio = img.width / img.height;
                    const canvasRatio = canvas.width / canvas.height;
                    let renderW, renderH, offsetX, offsetY;

                    if (imgRatio > canvasRatio) {{
                        renderH = canvas.height * 0.75;
                        renderW = renderH * imgRatio;
                    }} else {{
                        renderW = canvas.width * 0.85;
                        renderH = renderW / imgRatio;
                    }}

                    scale = 1.0 + Math.sin(step * 0.02) * 0.03;
                    const finalW = renderW * scale;
                    const finalH = renderH * scale;
                    
                    offsetX = (canvas.width - finalW) / 2;
                    offsetY = (canvas.height - finalH) / 2 - 30;

                    ctx.fillStyle = "#181818";
                    ctx.fillRect(0, 0, canvas.width, canvas.height);
                    
                    ctx.drawImage(img, offsetX, offsetY, finalW, finalH);

                    // 動態掃光特效
                    lightX += 5;
                    if (lightX > canvas.width * 2) lightX = -canvas.width;
                    const gradient = ctx.createLinearGradient(lightX, 0, lightX + 80, canvas.height);
                    gradient.addColorStop(0, 'rgba(255,255,255,0)');
                    gradient.addColorStop(0.5, 'rgba(255,255,255,0.18)');
                    gradient.addColorStop(1, 'rgba(255,255,255,0)');
                    ctx.fillStyle = gradient;
                    ctx.fillRect(0, 0, canvas.width, canvas.height);

                    // 縮小字體與安全區排版（避開 TikTok / 蝦皮介面按鈕）
                    const boxW = canvas.width - 60;
                    const boxH = 50;
                    const boxX = 30;
                    const boxY = canvas.height - 110;

                    ctx.fillStyle = "rgba(0,0,0,0.75)";
                    ctx.roundRect(boxX, boxY, boxW, boxH, 8);
                    ctx.fill();

                    ctx.fillStyle = "#FFFFFF";
                    ctx.font = "bold 13px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
                    const displayTitle = "{product_name}".length > 15 ? "{product_name}".substring(0, 15) + "..." : "{product_name}";
                    ctx.fillText(displayTitle, boxX + 12, boxY + 22);

                    ctx.fillStyle = "#FF5722";
                    ctx.font = "bold 12px sans-serif";
                    ctx.fillText("🔥 限時下殺 NT$ {price}", boxX + 12, boxY + 39);

                    step++;
                    requestAnimationFrame(drawFrame);
                }}

                function startRecording() {{
                    const btn = document.getElementById('recBtn');
                    btn.innerText = "⏳ 正在根據您的指令渲染影片...";
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
