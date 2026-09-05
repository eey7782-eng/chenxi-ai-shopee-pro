# -*- coding: utf-8 -*-
"""
黑金剛 AI 蝦皮半自動化 2.5 PRO
OpenAI API 主控版

功能：
- OpenAI Responses API 主控
- 商品文字 + 商品圖片分析
- 蝦皮標題/描述/賣點
- TikTok Hook/30 秒腳本
- 即夢 9:16 商品影片 Prompt
- 商品資料、素材、歷史紀錄 JSON 保存
- Streamlit Cloud Secrets
- 不自動登入/操作蝦皮帳號；發布前人工確認
"""

import base64
import io
import json
import os
import re
import traceback
from datetime import datetime
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

APP_NAME = "黑金剛 AI 蝦皮半自動化 2.5 PRO"
VERSION = "2.5 PRO — OpenAI API 主控版"
DATA_DIR = Path("data")
MEDIA_DIR = DATA_DIR / "media"
PRODUCTS_FILE = DATA_DIR / "products.json"
HISTORY_FILE = DATA_DIR / "history.json"
MEMBERS_FILE = DATA_DIR / "members.json"
MAX_IMAGE_MB = 20
MAX_IMAGE_SIZE = 1600
DEFAULT_MODEL = "gpt-5.6-luna"
CATEGORIES = ["保養美妝", "食品飲料", "居家生活", "3C 數位", "服飾鞋包", "母嬰用品", "寵物用品", "汽機車", "運動戶外", "其他"]

SYSTEM_PROMPT = """
你是「黑金剛 AI 蝦皮半自動化 2.5 PRO」的電商 AI 總控。
請使用台灣繁體中文。

核心規則：
1. 商品圖片是視覺事實來源。不要捏造品牌、Logo、包裝文字、規格、成分、認證、產地、功效。
2. 看不清楚或無法確認的資訊，放入 uncertain_items，不得當成事實。
3. 商品外觀、形狀、顏色、材質、Logo、標籤文字不可任意改造。
4. 不做醫療、治療、減肥等未證實效果承諾。
5. 蝦皮文案自然、可讀，不要關鍵字堆砌。
6. TikTok 腳本要適合 9:16 直式短影音。
7. 即夢影片 Prompt 要以參考商品為唯一主體，避免變形、亂字、亂 Logo。
8. 沒有影片 API 時，只產生 Prompt，不可聲稱影片已生成。
9. 最終必須輸出合法 JSON，不要 Markdown。
"""

OUTPUT_TEMPLATE = {
    "product_analysis": {
        "confirmed_facts": [],
        "visual_description": "",
        "category": "",
        "target_audience": "",
        "core_selling_points": [],
        "uncertain_items": []
    },
    "shopee": {
        "title": "",
        "short_title": "",
        "selling_points": [],
        "description": "",
        "search_keywords": [],
        "hashtags": []
    },
    "tiktok": {
        "hook": "",
        "script_30s": "",
        "caption": "",
        "hashtags": []
    },
    "image_prompt": "",
    "jimeng_prompt": "",
    "quality_check": []
}


def init_dirs():
    DATA_DIR.mkdir(exist_ok=True)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_json(path, default):
    try:
        if not path.exists():
            return default
        text = path.read_text(encoding="utf-8").strip()
        return json.loads(text) if text else default
    except Exception:
        return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def log(action, status, detail=None):
    rows = load_json(HISTORY_FILE, [])
    if not isinstance(rows, list):
        rows = []
    rows.insert(0, {"time": now(), "action": action, "status": status, "detail": detail or {}})
    save_json(HISTORY_FILE, rows[:500])


def secret(name, default=""):
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default)


def api_key():
    return secret("OPENAI_API_KEY", "").strip()


def model_name():
    return secret("OPENAI_MODEL", "").strip() or st.session_state.get("openai_model", DEFAULT_MODEL)


@st.cache_resource(show_spinner=False)
def openai_client(key):
    if not key or OpenAI is None:
        return None
    return OpenAI(api_key=key)


def api_status():
    if not api_key():
        return False, "OPENAI_API_KEY 尚未設定"
    if OpenAI is None:
        return False, "openai 套件尚未安裝"
    return True, f"OpenAI 已就緒：{model_name()}"


def image_normalize(upload):
    raw = upload.getvalue()
    if len(raw) > MAX_IMAGE_MB * 1024 * 1024:
        raise ValueError(f"圖片不可超過 {MAX_IMAGE_MB} MB")
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(raw)))
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGB")
    im.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE))
    out = io.BytesIO()
    if im.mode == "RGBA":
        im.save(out, "PNG", optimize=True)
        return out.getvalue(), "image/png", ".png"
    im.save(out, "JPEG", quality=92, optimize=True)
    return out.getvalue(), "image/jpeg", ".jpg"


def data_url(data, mime):
    return f"data:{mime};base64,{base64.b64encode(data).decode('utf-8')}"


def safe_filename(name):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name or "product.jpg")


def save_image(data, filename):
    path = MEDIA_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{safe_filename(filename)}"
    path.write_bytes(data)
    return str(path)


def detect_category(text):
    t = (text or "").lower()
    rules = {
        "保養美妝": ["洗面乳", "面膜", "精華", "乳液", "防曬", "口紅", "香水", "洗髮", "保養"],
        "食品飲料": ["芭樂", "水果", "咖啡", "茶", "飲料", "零食", "餅乾", "食品"],
        "居家生活": ["清潔", "收納", "水壺", "餐具", "家電", "拖把", "居家"],
        "3C 數位": ["手機", "平板", "耳機", "充電", "鍵盤", "滑鼠", "電腦", "相機"],
        "服飾鞋包": ["衣服", "上衣", "褲", "鞋", "包包", "帽", "襪"],
        "母嬰用品": ["嬰兒", "奶瓶", "尿布", "寶寶", "兒童"],
        "寵物用品": ["貓", "狗", "寵物", "貓砂", "飼料"],
        "汽機車": ["汽車", "機車", "車用", "行車記錄器"],
        "運動戶外": ["運動", "健身", "露營", "登山", "瑜伽"]
    }
    for cat, words in rules.items():
        if any(w in t for w in words):
            return cat
    return "其他"


def extract_json(text):
    text = (text or "").strip()
    for candidate in (text, re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I).strip()):
        try:
            return json.loads(candidate)
        except Exception:
            pass
    a, b = text.find("{"), text.rfind("}")
    if a >= 0 and b > a:
        return json.loads(text[a:b + 1])
    raise ValueError("OpenAI 回應不是有效 JSON")


def product_payload(p):
    return {
        "商品名稱": p.get("name", ""),
        "分類": p.get("category", ""),
        "價格": p.get("price", ""),
        "賣點": p.get("selling_points", ""),
        "商品連結": p.get("link", ""),
        "補充資訊": p.get("extra", "")
    }


def call_openai(product, image_bytes=None, image_mime="image/jpeg", task="full"):
    ok, msg = api_status()
    if not ok:
        raise RuntimeError(msg)
    client = openai_client(api_key())
    if client is None:
        raise RuntimeError("OpenAI Client 初始化失敗")

    task_text = {
        "full": "完整執行商品分析、蝦皮文案、TikTok 腳本、圖片 Prompt、即夢 Prompt。",
        "analysis": "只執行商品與圖片分析。",
        "shopee": "重點產出蝦皮標題、賣點、描述、關鍵字。",
        "tiktok": "重點產出 TikTok Hook、30 秒腳本、Caption、Hashtags。",
        "jimeng": "重點產出 9:16 商品影片 Prompt。"
    }.get(task, "完整執行所有任務。")

    prompt = f"""
{task_text}

商品資料：
{json.dumps(product_payload(product), ensure_ascii=False, indent=2)}

請按照此 JSON 結構輸出：
{json.dumps(OUTPUT_TEMPLATE, ensure_ascii=False, indent=2)}

只輸出 JSON。
"""
    content = [{"type": "input_text", "text": prompt}]
    if image_bytes:
        content.append({"type": "input_image", "image_url": data_url(image_bytes, image_mime), "detail": "high"})

    response = client.responses.create(
        model=model_name(),
        instructions=SYSTEM_PROMPT,
        input=[{"role": "user", "content": content}],
    )
    text = getattr(response, "output_text", "") or ""
    result = extract_json(text)
    st.session_state.last_ai_result = result
    return result


def fallback(product):
    name = product.get("name", "未命名商品")
    cat = product.get("category") or detect_category(name)
    point = product.get("selling_points") or "實用、適合日常使用"
    return {
        "product_analysis": {"confirmed_facts": [name], "visual_description": "尚未使用 OpenAI 視覺分析", "category": cat, "target_audience": "請依商品實際資訊判斷", "core_selling_points": [point], "uncertain_items": ["此為本地模板，不是 AI 分析結果"]},
        "shopee": {"title": f"{name}｜實用好物推薦", "short_title": name, "selling_points": [point], "description": f"{name}\n\n商品特色：\n{point}\n\n購買前請依實際商品資訊確認。", "search_keywords": [name, cat], "hashtags": ["#蝦皮", "#好物推薦"]},
        "tiktok": {"hook": f"今天分享：{name}", "script_30s": f"今天來看看 {name}。\n特色：{point}\n詳細資訊請以商品頁為準。", "caption": f"{name}｜好物分享", "hashtags": ["#好物分享", "#蝦皮"]},
        "image_prompt": f"以商品「{name}」為唯一主體的高質感電商攝影，保留參考商品真實外觀，9:16。",
        "jimeng_prompt": f"9:16 vertical premium product showcase for {name}; preserve the exact reference product appearance, packaging, colors, logo and visible text; smooth cinematic camera movement; realistic lighting; no distortion; no invented logo; no watermark.",
        "quality_check": ["本結果為本地模板，不代表 OpenAI 已分析。"]
    }


def products():
    data = load_json(PRODUCTS_FILE, [])
    return data if isinstance(data, list) else []


def save_products(data):
    save_json(PRODUCTS_FILE, data)


def add_product(p):
    rows = products()
    ids = [int(x.get("id", 0)) for x in rows if str(x.get("id", "")).isdigit()]
    p = dict(p)
    p.update({"id": max(ids or [0]) + 1, "created_at": now(), "updated_at": now(), "status": "待 AI 分析", "ai_result": {}})
    rows.append(p)
    save_products(rows)
    return p


def update_product(pid, updates):
    rows = products()
    for i, p in enumerate(rows):
        if str(p.get("id")) == str(pid):
            p.update(updates)
            p["updated_at"] = now()
            rows[i] = p
            save_products(rows)
            return p
    return None


def delete_product(pid):
    save_products([p for p in products() if str(p.get("id")) != str(pid)])


def run_workflow(product, image_bytes=None, image_mime="image/jpeg", task="full"):
    result = call_openai(product, image_bytes, image_mime, task)
    update_product(product["id"], {"status": "AI 分析完成", "ai_result": result, "analysis_time": now()})
    log("OpenAI AI 自動化", "完成", {"product_id": product["id"], "model": model_name(), "task": task})
    return result


def show_result(result):
    if not result:
        return
    a = result.get("product_analysis", {})
    s = result.get("shopee", {})
    t = result.get("tiktok", {})
    st.subheader("🧠 商品分析")
    c1, c2 = st.columns(2)
    with c1:
        st.write("**分類**", a.get("category", ""))
        st.write("**目標客群**", a.get("target_audience", ""))
    with c2:
        st.write("**確認資訊**")
        for x in a.get("confirmed_facts", []): st.write("•", x)
    st.subheader("🛒 蝦皮")
    st.text_input("標題", s.get("title", ""), key=f"title_{hash(json.dumps(result, ensure_ascii=False))}")
    st.text_area("描述", s.get("description", ""), height=240, key=f"desc_{hash(json.dumps(result, ensure_ascii=False))}")
    st.subheader("🎬 TikTok")
    st.text_input("Hook", t.get("hook", ""), key=f"hook_{hash(json.dumps(result, ensure_ascii=False))}")
    st.text_area("30 秒腳本", t.get("script_30s", ""), height=250, key=f"script_{hash(json.dumps(result, ensure_ascii=False))}")
    st.subheader("🎞️ 即夢 9:16 Prompt")
    st.text_area("Prompt", result.get("jimeng_prompt", ""), height=300, key=f"jimeng_{hash(json.dumps(result, ensure_ascii=False))}")


def dashboard():
    ps = products(); hs = load_json(HISTORY_FILE, [])
    st.title("🖤 黑金剛 AI 總控中心")
    st.caption(VERSION)
    c = st.columns(4)
    c[0].metric("商品", len(ps))
    c[1].metric("AI 完成", sum(p.get("status") == "AI 分析完成" for p in ps))
    c[2].metric("歷史", len(hs))
    ok, _ = api_status(); c[3].metric("OpenAI", "正常" if ok else "未設定")
    st.markdown("### 工作流")
    for n, title, detail in [(1,"上傳商品","商品資料 + 商品圖片"),(2,"OpenAI 分析","文字與視覺分析"),(3,"蝦皮","標題、賣點、描述"),(4,"TikTok","Hook、腳本、Caption"),(5,"即夢","9:16 影片 Prompt"),(6,"人工確認","確認後再發布")]:
        st.markdown(f"**{n}. {title}** — {detail}")


def workspace():
    st.header("🛒 商品上架工作台")
    with st.form("new_product"):
        a,b = st.columns(2)
        with a:
            name = st.text_input("商品名稱")
            price = st.text_input("價格", "999")
            category = st.selectbox("分類", ["自動判斷"] + CATEGORIES)
        with b:
            link = st.text_input("商品連結")
            selling = st.text_area("已確認賣點", height=120)
        extra = st.text_area("補充資訊", height=100)
        upload = st.file_uploader("商品圖片", type=["jpg","jpeg","png","webp"])
        go = st.form_submit_button("🚀 建立商品並執行 OpenAI", use_container_width=True)
    if not go: return
    if not name.strip(): st.error("請輸入商品名稱"); return
    if category == "自動判斷": category = detect_category(name + " " + selling)
    img = None; mime = "image/jpeg"; image_path = ""
    if upload:
        try:
            img, mime, _ = image_normalize(upload)
            image_path = save_image(img, upload.name)
        except Exception as e:
            st.error(str(e)); return
    p = add_product({"name":name.strip(),"price":price.strip(),"category":category,"selling_points":selling.strip(),"link":link.strip(),"extra":extra.strip(),"image_path":image_path})
    try:
        with st.spinner("OpenAI 分析中……"):
            result = run_workflow(p, img, mime)
        st.success("✅ 完成")
        show_result(result)
    except Exception as e:
        update_product(p["id"], {"status":"AI 分析失敗","ai_error":str(e)})
        log("OpenAI AI 自動化", "失敗", {"product_id":p["id"],"error":str(e)})
        st.error(str(e))


def product_management():
    st.header("📦 商品管理")
    ps = products()
    if not ps: st.info("尚無商品"); return
    for p in ps:
        pid=p.get("id")
        with st.expander(f"#{pid}｜{p.get('name','')}｜{p.get('status','')}"):
            st.write(f"分類：{p.get('category','')}｜價格：{p.get('price','')}")
            st.write(f"賣點：{p.get('selling_points','')}")
            x,y,z=st.columns(3)
            with x:
                if st.button("重新 AI 分析", key=f"r{pid}"):
                    data=None; mime="image/jpeg"; path=p.get("image_path","")
                    if path and Path(path).exists():
                        data=Path(path).read_bytes(); mime="image/png" if path.lower().endswith(".png") else "image/jpeg"
                    try: show_result(run_workflow(p,data,mime))
                    except Exception as e: st.error(str(e))
            with y:
                if st.button("本地模板", key=f"f{pid}"):
                    r=fallback(p); update_product(pid,{"status":"本地模板完成","ai_result":r}); show_result(r)
            with z:
                if st.button("刪除", key=f"d{pid}"):
                    delete_product(pid); log("刪除商品","完成",{"product_id":pid}); st.rerun()
            if p.get("ai_result"): show_result(p["ai_result"])


def automation():
    st.header("🤖 AI 自動化")
    ps=products()
    if not ps: st.info("請先建立商品"); return
    p=st.selectbox("商品",ps,format_func=lambda x:f"#{x.get('id')}｜{x.get('name')}")
    task_label=st.selectbox("任務",["完整","商品分析","蝦皮文案","TikTok","即夢 Prompt"])
    task={"完整":"full","商品分析":"analysis","蝦皮文案":"shopee","TikTok":"tiktok","即夢 Prompt":"jimeng"}[task_label]
    if st.button("🚀 執行",type="primary",use_container_width=True):
        data=None; mime="image/jpeg"; path=p.get("image_path","")
        if path and Path(path).exists(): data=Path(path).read_bytes(); mime="image/png" if path.lower().endswith(".png") else "image/jpeg"
        try:
            with st.spinner("OpenAI Agent 執行中……"): r=run_workflow(p,data,mime,task)
            show_result(r)
        except Exception as e: st.error(str(e))


def tiktok_page():
    st.header("🎬 TikTok 短影音")
    ps=products()
    if not ps: st.info("請先建立商品"); return
    p=st.selectbox("商品",ps,format_func=lambda x:f"#{x.get('id')}｜{x.get('name')}",key="ttp")
    r=p.get("ai_result",{}).get("tiktok",{})
    if not r: st.warning("尚無 AI 結果"); return
    st.text_input("Hook",r.get("hook","")); st.text_area("30 秒腳本",r.get("script_30s",""),height=300); st.text_area("Caption",r.get("caption",""),height=100); st.code(" ".join(r.get("hashtags",[])))
    st.info("本版不假裝影片已生成；可把腳本與 Prompt 交給你使用的影片工具。")


def jimeng_page():
    st.header("🎞️ 即夢 9:16 Prompt")
    ps=products()
    if not ps: st.info("請先建立商品"); return
    p=st.selectbox("商品",ps,format_func=lambda x:f"#{x.get('id')}｜{x.get('name')}",key="jp")
    r=p.get("ai_result",{}).get("jimeng_prompt","")
    if not r: st.warning("尚無 AI 結果"); return
    st.text_area("Prompt",r,height=450)
    st.markdown("**規則：** 保持商品外觀、包裝、Logo、可見文字一致；9:16；避免變形、亂字、亂 Logo、水印。")


def library():
    st.header("🗂️ AI 素材庫")
    for p in products():
        r=p.get("ai_result",{})
        if not r: continue
        with st.expander(f"#{p.get('id')}｜{p.get('name')}"):
            st.code(r.get("shopee",{}).get("title",""))
            st.code(r.get("image_prompt",""))
            st.code(r.get("jimeng_prompt",""))


def history_page():
    st.header("📜 歷史紀錄")
    rows=load_json(HISTORY_FILE,[])
    if not rows: st.info("尚無紀錄"); return
    for x in rows[:100]:
        st.write(f"**{x.get('time')}｜{x.get('action')}｜{x.get('status')}**")
        if x.get("detail"): st.json(x["detail"])


def api_page():
    st.header("🔐 OpenAI API 設定")
    st.warning("不要把 API Key 寫進 app.py 或 GitHub。")
    ok,msg=api_status()
    if ok: st.success(msg)
    else: st.error(msg)
    st.text_input("目前模型",model_name(),disabled=True)
    st.code('OPENAI_API_KEY = "你的 API Key"\nOPENAI_MODEL = "gpt-5.6-luna"',language="toml")
    if st.button("測試 OpenAI API",use_container_width=True):
        try:
            r=call_openai({"name":"測試商品","category":"居家生活","price":"999","selling_points":"實用","link":"","extra":""},task="analysis")
            st.success("✅ API 測試成功"); st.json(r)
        except Exception as e: st.error(str(e))


def system_page():
    st.header("🧪 系統檢查")
    ok,msg=api_status()
    st.success(f"Streamlit：{st.__version__}")
    st.success("Pillow：已安裝")
    st.success("OpenAI SDK：已安裝" if OpenAI else "OpenAI SDK：未安裝")
    st.success(msg) if ok else st.error(msg)
    st.write(f"商品：{len(products())}")
    st.code(VERSION)


def login():
    st.title("🖤 黑金剛 AI 2.5 PRO")
    st.caption("OpenAI API 主控版")
    members=load_json(MEMBERS_FILE,{})
    if "admin" not in members:
        members["admin"]={"password":"admin","role":"admin","created_at":now()}; save_json(MEMBERS_FILE,members)
    with st.form("login"):
        u=st.text_input("帳號"); p=st.text_input("密碼",type="password")
        if st.form_submit_button("登入",use_container_width=True):
            if u in members and p == members[u].get("password"):
                st.session_state.logged_in=True; st.session_state.username=u; st.rerun()
            else: st.error("帳號或密碼錯誤")
    st.info("測試帳號：admin / admin")


def main():
    st.set_page_config(page_title=APP_NAME,page_icon="🖤",layout="wide")
    init_dirs()
    for k,v in {"logged_in":False,"username":"","page":"Dashboard","openai_model":DEFAULT_MODEL,"last_ai_result":{}}.items():
        st.session_state.setdefault(k,v)
    if not st.session_state.logged_in:
        login(); return
    with st.sidebar:
        st.title("🖤 黑金剛")
        ok,msg=api_status(); st.success("● OpenAI 正常") if ok else st.warning("● OpenAI 未設定")
        st.session_state.page=st.radio("功能",["Dashboard","商品上架工作台","商品管理","AI 自動化","TikTok 短影音","即夢 Prompt","AI 素材庫","歷史紀錄","API 設定","系統檢查"])
        st.divider(); st.caption(f"登入：{st.session_state.username}")
        if st.button("登出",use_container_width=True): st.session_state.logged_in=False; st.rerun()
    try:
        pages={"Dashboard":dashboard,"商品上架工作台":workspace,"商品管理":product_management,"AI 自動化":automation,"TikTok 短影音":tiktok_page,"即夢 Prompt":jimeng_page,"AI 素材庫":library,"歷史紀錄":history_page,"API 設定":api_page,"系統檢查":system_page}
        pages[st.session_state.page]()
    except Exception as e:
        st.error(f"系統錯誤：{e}")
        with st.expander("錯誤詳細資訊"): st.code(traceback.format_exc())
        log("系統錯誤","失敗",{"error":str(e)})


if __name__ == "__main__":
    main()
