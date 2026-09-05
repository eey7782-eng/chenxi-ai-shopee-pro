# ============================================================
# 商品表單｜手機相簿穩定版
# ============================================================

def product_form(prefix="main"):

    st.markdown(
        '<div class="bk-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="bk-title">📦 商品資料</div>',
        unsafe_allow_html=True,
    )

    name = st.text_input(
        "商品名稱",
        placeholder="例如：甘草芭樂、UNO洗面乳、藍牙耳機",
        key=f"{prefix}_name",
    )

    auto_category = detect_product_category(name)

    categories = [
        "食品",
        "保養美妝",
        "3C",
        "居家生活",
        "服飾",
        "汽機車",
        "其他",
    ]

    default_index = (
        categories.index(auto_category)
        if auto_category in categories
        else 6
    )

    category = st.selectbox(
        "商品分類",
        categories,
        index=default_index,
        key=f"{prefix}_category",
    )

    col1, col2 = st.columns(2)

    with col1:

        price = st.number_input(
            "商品售價",
            min_value=0,
            value=999,
            step=1,
            key=f"{prefix}_price",
        )

    with col2:

        seconds = st.selectbox(
            "TikTok 影片秒數",
            [15, 30, 60],
            index=0,
            key=f"{prefix}_seconds",
        )

    points = st.text_area(
        "商品賣點",
        placeholder=(
            "輸入已確認的商品資訊。\n"
            "例如：容量、材質、功能、口味、尺寸、特色等。\n"
            "沒有資料的部分，AI 不得自行編造。"
        ),
        height=140,
        key=f"{prefix}_points",
    )

    # ========================================================
    # 手機／平板相簿上傳
    # ========================================================

    uploaded = st.file_uploader(
        "📷 上傳商品原圖",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
        ],
        accept_multiple_files=False,
        key=f"{prefix}_image",
        help="點擊後可直接選擇手機相簿中的照片。",
    )

    image_bytes = b""
    image_name = ""

    if uploaded is not None:

        try:

            image_bytes = uploaded.getvalue()
            image_name = uploaded.name

            # ----------------------------------------------
            # 檔案大小檢查
            # ----------------------------------------------

            file_size_mb = (
                len(image_bytes)
                / 1024
                / 1024
            )

            if file_size_mb > MAX_IMAGE_MB:

                st.error(
                    f"圖片太大：{file_size_mb:.1f} MB。"
                    f"請選擇 {MAX_IMAGE_MB} MB 以下的照片。"
                )

                image_bytes = b""

            else:

                # ------------------------------------------
                # 只讀取預覽
                # 不在這裡儲存檔案
                # ------------------------------------------

                image = Image.open(
                    io.BytesIO(image_bytes)
                )

                image = ImageOps.exif_transpose(
                    image
                )

                st.markdown(
                    "### 🖼️ 商品原圖預覽"
                )

                st.image(
                    image,
                    width=320,
                )

                st.success(
                    f"已選擇：{image_name}"
                )

        except Exception as e:

            image_bytes = b""

            st.error(
                "圖片讀取失敗，請重新選擇照片。"
            )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    return {
        "name": name.strip(),
        "category": category,
        "price": int(price),
        "points": points.strip(),
        "seconds": int(seconds),

        # 不直接存 UploadedFile
        "image_bytes": image_bytes,
        "image_name": image_name,
    }
