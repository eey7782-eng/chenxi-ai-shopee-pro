import os
import json
import time
import base64
import tempfile
from datetime import datetime
import requests
import streamlit as st
from openai import OpenAI

# ---------------------------------------------------------------------------
# 0. API 與系統基礎設定
# ---------------------------------------------------------------------------
KLING_BASE_URL = "https://api-singapore.klingai.com"

# ---------------------------------------------------------------------------
# 1. 頁面設定
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="蝦皮 AI 全自動上架與可靈系統 Pro+", 
    page_icon="🛒", 
    layout="wide"
)

# ---------------------------------------------------------------------------
# 2. 多媒體工具檢查
# ---------------------------------------------------------------------------
HAS_MEDIA_TOOLS = False
try:
    from PIL import Image
    import pillow_avif
    from moviepy.editor import ImageClip, concatenate_videoclips
    HAS_MEDIA_TOOLS = True
except ImportError:
    HAS_MEDIA_TOOLS = False
