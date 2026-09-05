import os, io, json, base64, hashlib, re
from pathlib import Path
from datetime import datetime, date, timedelta
import streamlit as st
from PIL import Image, ImageOps

APP_NAME = '黑金剛 AI 蝦皮半自動化 2.5 PRO'
APP_VERSION = '4.0'
DATA_DIR = Path('data'); HISTORY_DIR = DATA_DIR/'history'; PRODUCT_DIR = DATA_DIR/'products'; MEDIA_DIR = DATA_DIR/'media'; MEMBERS_FILE = DATA_DIR/'members.json'
for p in (DATA_DIR,HISTORY_DIR,PRODUCT_DIR,MEDIA_DIR): p.mkdir(parents=True, exist_ok=True)

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    genai = None; HAS_GENAI = False

MODELS = ['gemini-3.8-flash','gemini-3.7-flash','gemini-3.6-flash']
MAX_IMAGE_MB=20; MAX_VIDEO_MB=300; MAX_IMAGE_SIZE=1600

st.set_page_config(page_title=APP_NAME,page_icon='🥷',layout='wide',initial_sidebar_state='expanded')

for k,v in {'page':'Dashboard','gemini_model':'','gemini_error':'','analysis_result':'','shopee_result':'','jimeng_result':'','tiktok_result':'','current_product':{},'image_bytes':None,'image_mime':'image/jpeg','video_bytes':None,'video_name':'','logged_in':False,'username':'','is_admin':False}.items():
    st.session_state.setdefault(k,v)

st.markdown('''<style>
.stApp{background:#090909}.block-container{max-width:1500px;padding-top:1.2rem}.hero,.card{background:#131313;border:1px solid #2b2b2b;border-radius:18px;padding:22px;margin-bottom:16px}.hero-title{font-size:32px;font-weight:900}.hero-sub{color:#999;margin-top:7px}.workflow{display:grid;grid-template-columns:repeat(6,1fr);gap:10px}.step{background:#161616;border:1px solid #303030;border-radius:14px;padding:14px 8px;text-align:center}.step b{display:block;font-size:20px}.step span{font-size:12px;color:#aaa}.badge{padding:5px 10px;border-radius:99px;border:1px solid #444}.small{color:#999;font-size:13px}@media(max-width:800px){.workflow{grid-template-columns:repeat(2,1fr)}.hero-title{font-size:24px}}
</style>''',unsafe_allow_html=True)

def secret(name):
    try: x=st.secrets.get(name,'')
    except Exception: x=''
    return str(x or os.getenv(name,'')).strip()

def key_hash(x): return hashlib.sha256(x.encode()).hexdigest()
def load_json(p,default):
    try: return json.loads(Path(p).read_text(encoding='utf-8'))
    except Exception: return default
def save_json(p,obj): Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

def members(): return load_json(MEMBERS_FILE,{})
def ensure_admin():
    m=members()
    if 'admin' not in m:
        m['admin']={'password_hash':key_hash('admin123'),'expires':None,'admin':True,'created':datetime.now().isoformat()}
        save_json(MEMBERS_FILE,m)
ensure_admin()

def login(u,p):
    m=members().get(u)
    if not m or m.get('password_hash')!=key_hash(p): return False,'帳號或密碼錯誤'
    if m.get('expires'):
        try:
            if date.today()>date.fromisoformat(m['expires']): return False,'會員已到期'
        except ValueError: pass
    st.session_state.logged_in=True; st.session_state.username=u; st.session_state.is_admin=bool(m.get('admin')); return True,'登入成功'

def register(u,p):
    if not re.fullmatch(r'[A-Za-z0-9_.-]{3,30}',u or ''): return False,'帳號需 3～30 字，只能英文、數字、_、.、-'
    if len(p or '')<6: return False,'密碼至少 6 碼'
    m=members()
    if u in m:return False,'帳號已存在'
    m[u]={'password_hash':key_hash(p),'expires':(date.today()+timedelta(days=30)).isoformat(),'admin':False,'created':datetime.now().isoformat()};save_json(MEMBERS_FILE,m);return True,'註冊完成，有效期 30 天'

def gemini_client():
    if not HAS_GENAI or not secret('GEMINI_API_KEY'): return None
    try:return genai.Client(api_key=secret('GEMINI_API_KEY'))
    except Exception as e: st.session_state.gemini_error=str(e);return None

@st.cache_resource
def cached_client(): return gemini_client()

def call_gemini(prompt,image=None,mime='image/jpeg'):
    c=cached_client()
    if c is None: st.session_state.gemini_error='請安裝 google-genai 並設定 GEMINI_API_KEY';return None
    inp=prompt
    if image:
        inp=[{'type':'image','mime_type':mime,'data':base64.b64encode(image).decode('utf-8')},{'type':'text','text':prompt}]
    last=''
    for model in MODELS:
        try:
            r=c.interactions.create(model=model,input=inp)
            text=getattr(r,'output_text',None)
            if text:
                st.session_state.gemini_model=model;st.session_state.gemini_error='';return text.strip()
        except Exception as e:last=str(e)
    st.session_state.gemini_error=last or 'Gemini 沒有回傳內容';return None

def category(t):
    mp={'食品':['芭樂','水果','零食','食品','茶','咖啡','糖'],'保養美妝':['洗面','乳液','精華','面膜','保養','彩妝','口紅'],'3C':['手機','平板','耳機','充電','鍵盤','滑鼠','電腦'],'居家生活':['收納','清潔','居家','廚房','杯','鍋'],'服飾':['衣','褲','鞋','襪','外套','包包','帽'],'汽機車':['汽車','機車','車用','雨刷','機油']}
    for c,ws in mp.items():
        if any(w.lower() in (t or '').lower() for w in ws):return c
    return '其他'

RULES='''商品圖片是商品外觀、品牌、Logo、包裝、顏色、形狀、材質與圖片文字的最高優先來源。只能使用圖片或使用者明確提供且不衝突的資料。無法確認就寫「圖片無法確認」。禁止虛構品牌、Logo、型號、規格、容量、重量、尺寸、成分、功效、認證、產地或圖片文字。若資料與圖片衝突，標示「⚠️ 商品資料與圖片可能不一致」。影片必須保持原商品外觀，不得改品牌、Logo、包裝、顏色、形狀、材質或文字。'''

def analysis_prompt(p):
    return f'''你是黑金剛電商商品分析 AI。\n商品名稱：{p["name"]}\n分類：{p["category"]}\n價格：{p["price"]}\n使用者賣點：{p["selling"]}\n\n{RULES}\n\n請輸出：商品分析、圖片辨識、商品類型、品牌、Logo、外觀、顏色、材質、包裝、圖片文字、可確認賣點、蝦皮SEO標題、蝦皮商品描述、短版銷售文案、TikTok Hook、TikTok 15秒腳本、TikTok 30秒腳本、即夢AI 2.5 Prompt、不確定資訊、圖片與資料衝突檢查。''' 

def shopee_prompt(p,a): return f'''你是台灣蝦皮電商文案專家。商品：{p["name"]}；分類：{p["category"]}；價格：{p["price"]}；賣點：{p["selling"]}。分析：{a}\n{RULES}\n輸出蝦皮SEO標題、商品描述、商品特色、主要賣點、使用情境、注意事項、短版文案、TikTok Hook、15秒腳本、30秒腳本、關鍵字。不得虛構商品資訊。'''

def tiktok_prompt(p,a): return f'''根據商品「{p["name"]}」與分析製作台灣TikTok短影音：{a}\n{RULES}\n輸出3個Hook、15秒腳本、30秒腳本、字幕、口播、鏡頭、CTA、Hashtags。影片比例9:16，1080x1920。'''

def jimeng_prompt(p,a): return f'''你是黑金剛即夢AI 2.5商品影片Prompt專家。商品：{p["name"]}。分析：{a}\n{RULES}\n建立15秒9:16、1080x1920高級商業商品廣告Prompt：0-3秒建立場景、3-6秒慢速推鏡、6-9秒輕微環繞、9-12秒細節特寫、12-15秒英雄鏡頭。電影級燈光、真實材質、淺景深、乾淨背景。只輸出完整Prompt。'''

def save_history(p):
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S_%f');save_json(HISTORY_DIR/f'{stamp}.json',p)

def login_page():
    st.markdown(f'<div class="hero"><div class="hero-title">🥷 {APP_NAME}</div><div class="hero-sub">商品分析 → 指令碼圖 → 蝦皮 → TikTok → 即夢 → 商品影片</div></div>',unsafe_allow_html=True)
    a,b=st.columns(2)
    with a:
        st.subheader('🔐 會員登入');u=st.text_input('帳號',key='lu');p=st.text_input('密碼',type='password',key='lp')
        if st.button('登入',type='primary',use_container_width=True):
            ok,msg=login(u,p);st.success(msg) if ok else st.error(msg)
            if ok:st.rerun()
    with b:
        st.subheader('👤 註冊會員');u=st.text_input('新帳號',key='ru');p=st.text_input('新密碼',type='password',key='rp')
        if st.button('註冊',use_container_width=True):
            ok,msg=register(u,p);st.success(msg) if ok else st.error(msg)
        st.caption('預設管理員：admin / admin123')

if not st.session_state.logged_in:
    login_page();st.stop()

with st.sidebar:
    st.markdown('## 🥷 黑金剛');st.caption(APP_VERSION);st.divider()
    items=['Dashboard','商品上架工作台','商品指令碼圖','商品影片製作','商品管理','TikTok短影音','AI素材庫','歷史紀錄','數據分析','蝦皮分潤管理']
    if st.session_state.is_admin:items.append('管理員中心')
    menu=st.radio('功能',items);st.session_state.page=menu;st.divider()
    if HAS_GENAI and secret('GEMINI_API_KEY'):
        st.success('Gemini API 已設定');st.caption(st.session_state.gemini_model or '自動 3.8 → 3.7 → 3.6')
    else:st.warning('Gemini API 未設定')
    if st.session_state.gemini_error:
        with st.expander('Gemini 錯誤'):st.code(st.session_state.gemini_error)
    if st.button('🚪 登出',use_container_width=True): st.session_state.logged_in=False;st.rerun()

st.markdown(f'<div class="hero"><div class="hero-title">🥷 {APP_NAME}</div><div class="hero-sub">完整商品工作流｜手機／平板友善</div></div>',unsafe_allow_html=True)

if menu=='Dashboard':
    st.header('🏠 Dashboard');a,b,c,d=st.columns(4);a.metric('AI狀態','ONLINE' if secret('GEMINI_API_KEY') and HAS_GENAI else 'OFFLINE');b.metric('Gemini',st.session_state.gemini_model or 'AUTO');c.metric('商品',len(list(PRODUCT_DIR.glob('*.json'))));d.metric('歷史',len(list(HISTORY_DIR.glob('*.json'))))
    st.markdown('''<div class="workflow"><div class="step"><b>🖼️</b><span>商品原圖</span></div><div class="step"><b>🔍</b><span>Gemini分析</span></div><div class="step"><b>🧩</b><span>商品指令碼圖</span></div><div class="step"><b>🛒</b><span>蝦皮上架</span></div><div class="step"><b>🎵</b><span>TikTok</span></div><div class="step"><b>🎬</b><span>即夢＋影片</span></div></div>''',unsafe_allow_html=True)

elif menu=='商品上架工作台':
    st.header('📦 商品上架工作台');a,b=st.columns([1,1])
    with a:
        name=st.text_input('商品名稱',placeholder='例如：甘草芭樂');cat=st.selectbox('商品分類',['食品','保養美妝','3C','居家生活','服飾','汽機車','其他'],index=['食品','保養美妝','3C','居家生活','服飾','汽機車','其他'].index(category(name)));price=st.number_input('商品價格',min_value=0,value=999);selling=st.text_area('商品賣點',height=130)
    with b:
        up=st.file_uploader('商品原圖',type=['jpg','jpeg','png','webp'])
        if up:
            raw=up.getvalue();
            if len(raw)>MAX_IMAGE_MB*1024*1024:st.error(f'圖片不可超過{MAX_IMAGE_MB}MB')
            else:
                try:
                    im=ImageOps.exif_transpose(Image.open(io.BytesIO(raw)));im.thumbnail((MAX_IMAGE_SIZE,MAX_IMAGE_SIZE));o=io.BytesIO();im.convert('RGB').save(o,'JPEG',quality=92);st.session_state.image_bytes=o.getvalue();st.session_state.image_mime='image/jpeg';st.image(st.session_state.image_bytes,caption='商品原圖',use_container_width=True)
                except Exception as e:st.error(f'圖片處理失敗：{e}')
    if st.button('🚀 Gemini 完整分析商品',type='primary',use_container_width=True):
        if not st.session_state.image_bytes:st.error('請先上傳商品圖片')
        elif not secret('GEMINI_API_KEY'):st.error('請在 Streamlit Secrets 設定 GEMINI_API_KEY')
        else:
            p={'name':name or '未命名商品','category':cat,'price':price,'selling':selling,'created':datetime.now().isoformat()}
            with st.spinner('Gemini 正在分析商品圖片...'):r=call_gemini(analysis_prompt(p),st.session_state.image_bytes,st.session_state.image_mime)
            if r:st.session_state.current_product=p;st.session_state.analysis_result=r;save_json(PRODUCT_DIR/f'{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}.json',p);st.success('分析完成')
    if st.session_state.analysis_result:
        st.text_area('🤖 商品AI分析',st.session_state.analysis_result,height=620)
        a,b,c=st.columns(3)
        if a.button('🛒 產生蝦皮文案',use_container_width=True):
            p=st.session_state.current_product;r=call_gemini(shopee_prompt(p,st.session_state.analysis_result));
            if r:st.session_state.shopee_result=r;save_history({'product':p,'analysis':st.session_state.analysis_result,'shopee':r})
        if b.button('🎬 產生即夢2.5 Prompt',use_container_width=True):
            p=st.session_state.current_product;r=call_gemini(jimeng_prompt(p,st.session_state.analysis_result));
            if r:st.session_state.jimeng_result=r
        if c.button('🎵 產生TikTok腳本',use_container_width=True):
            p=st.session_state.current_product;r=call_gemini(tiktok_prompt(p,st.session_state.analysis_result));
            if r:st.session_state.tiktok_result=r
        if st.session_state.shopee_result:st.text_area('🛒 蝦皮文案',st.session_state.shopee_result,height=450)
        if st.session_state.tiktok_result:st.text_area('🎵 TikTok腳本',st.session_state.tiktok_result,height=450)
        if st.session_state.jimeng_result:st.text_area('🎬 即夢AI 2.5 Prompt',st.session_state.jimeng_result,height=450)

elif menu=='商品指令碼圖':
    st.header('🧩 商品指令碼圖');p=st.session_state.current_product
    if not p:st.info('請先建立商品')
    else:
        st.markdown(f'### {p["name"]}')
        st.markdown('''<div class="workflow"><div class="step"><b>01</b><span>商品原圖<br>唯一來源</span></div><div class="step"><b>02</b><span>Gemini<br>視覺分析</span></div><div class="step"><b>03</b><span>商品定位<br>賣點</span></div><div class="step"><b>04</b><span>蝦皮<br>SEO文案</span></div><div class="step"><b>05</b><span>TikTok<br>15/30秒</span></div><div class="step"><b>06</b><span>即夢2.5<br>影片Prompt</span></div></div>''',unsafe_allow_html=True)
        st.markdown('<div class="card"><b>🎥 商品影片指令流程</b><br>原圖 → 商品辨識 → 保持品牌/Logo/包裝 → 場景建立 → 推鏡 → 環繞 → 細節特寫 → 英雄鏡頭 → 9:16影片</div>',unsafe_allow_html=True)
        if st.session_state.analysis_result:st.text_area('商品指令碼',st.session_state.analysis_result,height=500)
        if st.session_state.jimeng_result:st.text_area('即夢影片指令',st.session_state.jimeng_result,height=500)

elif menu=='商品影片製作':
    st.header('🎥 商品影片製作中心');st.caption('9:16｜1080×1920｜整理原圖、指令碼、即夢Prompt與成品影片')
    if st.session_state.image_bytes:st.image(st.session_state.image_bytes,caption='原始商品圖',use_container_width=True)
    up=st.file_uploader('上傳製作完成的商品影片',type=['mp4','mov','webm'])
    if up:
        if len(up.getvalue())>MAX_VIDEO_MB*1024*1024:st.error(f'影片不可超過{MAX_VIDEO_MB}MB')
        else:
            st.session_state.video_bytes=up.getvalue();st.session_state.video_name=up.name;st.video(st.session_state.video_bytes);st.download_button('⬇️ 下載影片',st.session_state.video_bytes,file_name=up.name,mime=up.type,use_container_width=True)
    a,b=st.columns(2)
    with a:
        st.subheader('🎬 即夢AI 2.5');st.text_area('Prompt',st.session_state.jimeng_result or '尚未產生',height=500)
    with b:
        st.subheader('🎵 影片腳本');st.text_area('Script',st.session_state.tiktok_result or '尚未產生',height=500)

elif menu=='商品管理':
    st.header('📦 商品管理')
    fs=sorted(PRODUCT_DIR.glob('*.json'),reverse=True)
    if not fs:st.info('尚無商品')
    for f in fs[:100]:
        p=load_json(f,{})
        with st.expander(f'{p.get("name","未命名")}｜{p.get("created","")}'):
            st.json(p)
            if st.button('載入',key='load_'+f.name):st.session_state.current_product=p;st.success('已載入')

elif menu=='TikTok短影音':
    st.header('🎵 TikTok短影音');p=st.session_state.current_product
    if not p or not st.session_state.analysis_result:st.info('請先完成商品分析')
    else:
        if st.button('✨ 重新產生15/30秒腳本',type='primary',use_container_width=True):
            r=call_gemini(tiktok_prompt(p,st.session_state.analysis_result));
            if r:st.session_state.tiktok_result=r
        if st.session_state.tiktok_result:
            st.text_area('TikTok完整腳本',st.session_state.tiktok_result,height=650);st.download_button('⬇️下載腳本',st.session_state.tiktok_result,'tiktok_script.txt')

elif menu=='AI素材庫':
    st.header('🗂️ AI素材庫')
    if st.session_state.image_bytes:st.image(st.session_state.image_bytes,use_container_width=True)
    if st.session_state.jimeng_result:st.text_area('即夢Prompt',st.session_state.jimeng_result,height=450)
    if st.session_state.tiktok_result:st.text_area('TikTok腳本',st.session_state.tiktok_result,height=450)

elif menu=='歷史紀錄':
    st.header('🕘 歷史紀錄');fs=sorted(HISTORY_DIR.glob('*.json'),reverse=True)
    if not fs:st.info('尚無紀錄')
    for i,f in enumerate(fs[:100]):
        r=load_json(f,{})
        with st.expander(f'{r.get("product",{}).get("name","商品")}｜{f.stem}'):
            st.json(r)

elif menu=='數據分析':
    st.header('📊 數據分析');a,b,c=st.columns(3);a.metric('商品',len(list(PRODUCT_DIR.glob('*.json'))));b.metric('歷史',len(list(HISTORY_DIR.glob('*.json'))));c.metric('會員',len(members()))

elif menu=='蝦皮分潤管理':
    st.header('💰 蝦皮分潤管理');a,b,c=st.columns(3);price=a.number_input('成交價',min_value=0.0,value=999.0);rate=b.number_input('分潤率 %',min_value=0.0,max_value=100.0,value=5.0);qty=c.number_input('成交數量',min_value=0,value=1);st.metric('預估分潤',f'NT$ {price*qty*rate/100:,.0f}')

elif menu=='管理員中心':
    if not st.session_state.is_admin:st.error('沒有權限')
    else:
        st.header('🛡️ 管理員中心');m=members();st.metric('會員數',len(m))
        for u,x in m.items():
            with st.expander(u):
                st.write('管理員：',bool(x.get('admin')));st.write('到期日：',x.get('expires') or '永久');st.write('建立：',x.get('created'))
                if u!='admin' and st.button('設為永久會員',key='p_'+u):m[u]['expires']=None;save_json(MEMBERS_FILE,m);st.success('已更新');st.rerun()

st.caption(f'{APP_NAME} v{APP_VERSION}｜Gemini Interactions API')
