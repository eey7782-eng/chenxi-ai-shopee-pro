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
    st.title("🔥 蝦皮獨家爆款 AI 戰術系統 (9:16 可下載影片版)")
    
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
        uploaded_file = st.file_uploader("上傳商品圖片 (選填)", type=["jpg", "jpeg", "png"])
        
        btn = st.button("🚀 生成戰術行銷包 + 9:16 影片", type="primary", use_container_width=True)

    with col2:
        if btn:
            with st.spinner("AI 正在分析競品痛點並生成文案..."):
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
5. 🎨 Midjourney / Runway 專用英文 Prompt
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

            # 9:16 畫質渲染與 MP4 匯出引擎
            st.divider()
            st.subheader("🎥 6. 9:16 直立式短影音合成與下載")
            
            if uploaded_file:
                img_data = base64.b64encode(uploaded_file.getvalue()).decode()
                img_src = f"data:{uploaded_file.type};base64,{img_data}"
            else:
                image_prompt = f"commercial product shot of {product_name}, luxury studio lighting, high resolution, 4k"
                img_src = f"https://pollinations.ai/p/{image_prompt.replace(' ', '%20')}?width=720&height=1280&seed=42&model=flux"

            # 9:16 Canvas 畫面繪製與動態錄影元件
            html_code = f"""
            <div style="display: flex; flex-direction: column; align-items: center; gap: 15px;">
                <canvas id="videoCanvas" width="360" height="640" style="border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); background: #000;"></canvas>
                <div style="display: flex; gap: 10px;">
                    <button id="recBtn" onclick="startRecording()" style="padding: 10px 20px; background: #FF4B4B; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">🎥 渲染 9:16 動態影片</button>
                    <a id="downloadLink" style="display: none; padding: 10px 20px; background: #00C853; color: white; border-radius: 8px; font-weight: bold; text-decoration: none;">📥 下載 9:16 宣傳影片 (.mp4)</a>
                </div>
            </div>

            <script>
                const canvas = document.getElementById('videoCanvas');
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
                    
                    // 1. 3D 鏡頭推軌效果 (Scale & Pan)
                    scale = 1.0 + Math.sin(step * 0.02) * 0.08;
                    const sw = canvas.width * scale;
                    const sh = canvas.height * scale;
                    const sx = (canvas.width - sw) / 2;
                    const sy = (canvas.height - sh) / 2;
                    ctx.drawImage(img, sx, sy, sw, sh);

                    // 2. 掃光特效
                    lightX += 6;
                    if (lightX > canvas.width * 2) lightX = -canvas.width;
                    const gradient = ctx.createLinearGradient(lightX, 0, lightX + 100, canvas.height);
                    gradient.addColorStop(0, 'rgba(255,255,255,0)');
                    gradient.addColorStop(0.5, 'rgba(255,255,255,0.3)');
                    gradient.addColorStop(1, 'rgba(255,255,255,0)');
                    ctx.fillStyle = gradient;
                    ctx.fillRect(0, 0, canvas.width, canvas.height);

                    // 3. 9:16 爆款字卡 overlay
                    ctx.fillStyle = "rgba(0,0,0,0.65)";
                    ctx.roundRect(20, canvas.height - 100, canvas.width - 40, 70, 12);
                    ctx.fill();

                    ctx.fillStyle = "#FFFFFF";
                    ctx.font = "bold 18px sans-serif";
                    ctx.fillText("{product_name}", 35, canvas.height - 65);
                    ctx.fillStyle = "#FFD700";
                    ctx.font = "14px sans-serif";
                    ctx.fillText("🔥 限時優惠 NT$ {price}", 35, canvas.height - 40);

                    step++;
                    requestAnimationFrame(drawFrame);
                }}

                function startRecording() {{
                    const btn = document.getElementById('recBtn');
                    btn.innerText = "⏳ 正在生成 5秒 影片...";
                    btn.disabled = true;

                    const stream = canvas.captureStream(30);
                    const mediaRecorder = new MediaRecorder(stream, {{ mimeType: 'video/webm' }});
                    let chunks = [];

                    mediaRecorder.ondataavailable = e => chunks.push(e.data);
                    mediaRecorder.onstop = e => {{
                        const blob = new Blob(chunks, {{ type: 'video/mp4' }});
                        const url = URL.createObjectURL(blob);
                        const a = document.getElementById('downloadLink');
                        a.href = url;
                        a.download = "{product_name}_9x16_promo.mp4";
                        a.style.display = "inline-block";
                        btn.innerText = "✅ 渲染完成！";
                    }};

                    mediaRecorder.start();
                    setTimeout(() => mediaRecorder.stop(), 5000); // 錄製 5 秒爆款短影音
                }}
            </script>
            """
            st.components.v1.html(html_code, height=720)
