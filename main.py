import os, json, logging, urllib.parse, re, unicodedata, requests
import yt_dlp
import tempfile
import asyncio

from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# ========= ENV =========
ENV_PATH = Path(__file__).with_name(".env")
load_dotenv(ENV_PATH)

TOKEN      = os.getenv("TOKEN")
YT_API_KEY = os.getenv("YT_API_KEY", "")
ADMIN_ID   = int(os.getenv("ADMIN_ID", "0"))
GEMINI_KEY = os.getenv("GEMINI_KEY", "")

if not TOKEN:
    raise SystemExit("TOKEN missing in .env")

# ========= Telegram imports =========
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, InputFile
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# ========= Logging =========
logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO)
log = logging.getLogger("musicbot")

# ========= State & Simple analytics =========
user_mode: Dict[int, str] = {}   # user_id -> "music" | "ai"
USER_PREFS: Dict[int, Dict[str, str]] = {}  # user_id -> {"source": "youtube"/"apple", "country": "eg"}
USERS_PATH = Path(__file__).with_name("users.json")
USERS: Dict[str, Dict[str, str]] = {}

def load_users():
    global USERS
    if USERS_PATH.exists():
        try:
            USERS = json.loads(USERS_PATH.read_text(encoding="utf-8"))
        except Exception:
            USERS = {}

def save_users():
    try:
        USERS_PATH.write_text(json.dumps(USERS, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        log.warning("Saving users failed: %s", e)

def touch_user(update: Update):
    u = update.effective_user
    if not u: return
    uid = str(u.id)
    USERS.setdefault(uid, {})
    USERS[uid]["username"]   = u.username or ""
    USERS[uid]["first_name"] = u.first_name or ""
    USERS[uid]["last_name"]  = u.last_name or ""
    save_users()

def set_pref(uid: int, key: str, val: str):
    USER_PREFS.setdefault(uid, {})[key] = val

def get_pref(uid: int, key: str, default: Optional[str]=None) -> Optional[str]:
    return USER_PREFS.get(uid, {}).get(key, default)

# ========= Utils =========

def norm_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).replace("ـ","")
    s = re.sub(r"\s+"," ",s).strip()
    return s


def main_menu(user_id: Optional[int] = None) -> ReplyKeyboardMarkup:
    kb = [
        ["🎵 أغاني", "🤖 AI Chat"],
        ["🎯 Source: YouTube", "🎯 Source: Apple"],
        ["🌍 Country: EG", "🌍 Country: US"],
    ]
    # Admin-only row (hidden for others)
    if ADMIN_ID and user_id == ADMIN_ID:
        kb.append(["🗂 /to_m4a", " /stats", "/whoami"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)


def source_choice_kb(query: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🍎 Apple",  callback_data=f"src|apple|{urllib.parse.quote(query)}"),
        InlineKeyboardButton("▶️ YouTube", callback_data=f"src|youtube|{urllib.parse.quote(query)}"),
    ]])

# ========= Title normalization & de-dup helpers =========
BAD_WORDS = {
    "official video", "official audio", "audio", "lyrics", "lyric video",
    "visualizer", "remaster", "remastered", "hd", "hq", "mv", "music video",
    "color coded", "arabic lyrics", "english lyrics", "arabic sub", "arabic",
    "karaoke", "cover", "sped up", "slowed", "nightcore", "8d", "4k", "live"
}

def norm_song_title(raw: str) -> str:
    if not raw:
        return ""
    s = raw.lower()
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"\[[^\]]*\]", " ", s)
    s = re.sub(r"\{[^}]*\}", " ", s)
    s = s.replace("—", "-").replace("–", "-").replace("|", " ")
    for w in BAD_WORDS:
        s = re.sub(rf"\b{re.escape(w)}\b", " ", s)
    s = re.sub(r"[^a-z0-9\u0621-\u064A\s\-]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def dedup_youtube(items: List[Dict[str, str]], limit=5) -> List[Dict[str, str]]:
    seen = set()
    out = []
    for it in items:
        base = norm_song_title(it.get("title",""))
        key = f"{base}|{(it.get('channel') or '').lower()}"
        if base and key not in seen:
            seen.add(key)
            out.append(it)
        if len(out) >= limit:
            break
    return out


def dedup_apple(items: List[Dict[str, Any]], limit=10) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for t in items:
        title = norm_song_title(t.get("trackName",""))
        artist = (t.get("artistName","") or "").lower()
        key = f"{title}|{artist}"
        if title and key not in seen:
            seen.add(key)
            out.append(t)
        if len(out) >= limit:
            break
    return out

# ========= YouTube (Data API search; Music-only + dedupe) =========

def yt_api_search(query: str, max_results: int = 12) -> List[Dict[str, str]]:
    if not YT_API_KEY:
        return []
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": YT_API_KEY,
        "q": query,
        "type": "video",
        "part": "snippet",
        "maxResults": max_results,
        "safeSearch": "none",
        "videoCategoryId": "10",   # Music
        "topicId": "/m/04rlf"      # Music topic
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        raw = []
        for item in data.get("items", []):
            vid = item["id"]["videoId"]
            title = item["snippet"]["title"]
            channel = item["snippet"].get("channelTitle", "")
            raw.append({
                "url": f"https://www.youtube.com/watch?v={vid}",
                "title": title,
                "channel": channel
            })
        return dedup_youtube(raw, limit=5)
    except Exception as e:
        log.warning("YouTube API error: %s", e)
        return []


def listen_kb_youtube(url: str, title: str) -> InlineKeyboardMarkup:
    encoded_url = urllib.parse.quote(url)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Listen now (YouTube)", callback_data=f"yt_dl|{encoded_url}")],
        [InlineKeyboardButton("🔗 Open link", url=url),
         InlineKeyboardButton("🔎 Search again", switch_inline_query_current_chat=title)]
    ])

# ========= Apple (iTunes 30s preview) =========
ITUNES_SEARCH = "https://itunes.apple.com/search"
ITUNES_LOOKUP = "https://itunes.apple.com/lookup"
COUNTRY_ORDER = ["eg","sa","ae","ma","us","gb"]


def itunes_search(term: str, country: str, limit=8, attribute: Optional[str]=None) -> List[Dict[str, Any]]:
    params = {"term": term, "entity": "song", "limit": limit, "country": country}
    if attribute: params["attribute"] = attribute
    r = requests.get(ITUNES_SEARCH, params=params, timeout=15)
    r.raise_for_status()
    return r.json().get("results", [])


def itunes_lookup(track_id: int) -> Optional[Dict[str, Any]]:
    r = requests.get(ITUNES_LOOKUP, params={"id": track_id}, timeout=15)
    r.raise_for_status()
    arr = r.json().get("results", [])
    return arr[0] if arr else None


def unique_by_trackid(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen=set(); out=[]
    for t in items:
        tid = t.get("trackId")
        if tid and tid not in seen:
            seen.add(tid); out.append(t)
    return out


def score_match(query: str, t: Dict[str, Any]) -> float:
    q = query.lower()
    name = (t.get("trackName") or "").lower()
    artist = (t.get("artistName") or "").lower()
    score = 0.0
    if q in name: score += 3
    if q in (name + " " + artist): score += 3
    q_tokens = set(q.split())
    score += len(q_tokens & set(name.split())) * 1.5
    score += len(q_tokens & set(artist.split())) * 1.0
    return score


def best_n(query: str, tracks: List[Dict[str, Any]], n=6) -> List[Dict[str, Any]]:
    return sorted(tracks, key=lambda t: score_match(query, t), reverse=True)[:n]


def comprehensive_apple_search(user_id: int, raw_query: str, limit_each=6) -> List[Dict[str, Any]]:
    q = norm_text(raw_query)
    user_country = get_pref(user_id, "country")
    countries = [user_country] + [c for c in COUNTRY_ORDER if c != user_country] if user_country else COUNTRY_ORDER[:]
    results: List[Dict[str, Any]] = []
    for c in countries:
        try: results += itunes_search(q, c, limit=limit_each, attribute="songTerm")
        except: pass
    for c in countries:
        try: results += itunes_search(q, c, limit=limit_each, attribute="artistTerm")
        except: pass

    ranked = best_n(q, unique_by_trackid(results), n=30)
    return dedup_apple(ranked, limit=10)


def fmt_track_line(t: Dict[str, Any]) -> str:
    name = t.get("trackName", "Unknown"); artist = t.get("artistName", "Unknown")
    album = t.get("collectionName", "")
    return f"• {name} — {artist}" + (f" ({album})" if album else "")


def kb_for_track(t: Dict[str, Any]) -> InlineKeyboardMarkup:
    tid = t["trackId"]
    song = t.get("trackName", ""); artist = t.get("artistName","")
    yt_q = urllib.parse.quote(f"{song} {artist}".strip())
    btns = [
        [InlineKeyboardButton("▶️ Listen now", callback_data=f"play|{tid}")],
        [InlineKeyboardButton("🔗 Open on Apple", url=t.get("trackViewUrl",""))],
        [InlineKeyboardButton("▶️ YouTube for this", url=f"https://www.youtube.com/results?q={yt_q}")]
    ]
    return InlineKeyboardMarkup(btns)

# ========= File → m4a (uploads only) =========
from pydub import AudioSegment
async def to_m4a_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    touch_user(update)
    if ADMIN_ID and (not update.effective_user or update.effective_user.id != ADMIN_ID):
        await update.message.reply_text("الأمر /to_m4a متاح للمالك فقط.")
        return
    await update.message.reply_text("ابعت ملف صوت/فيديو تملكه، وأنا هرجّعه لك m4a. لازم FFmpeg يكون متثبت.")

async def to_m4a_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    touch_user(update)
    if ADMIN_ID and (not update.effective_user or update.effective_user.id != ADMIN_ID):
        await update.message.reply_text("رفع الملفات للتحويل متاح للمالك فقط.")
        return
    file_obj = update.message.audio or update.message.voice or update.message.video or update.message.document
    if not file_obj:
        await update.message.reply_text("من فضلك ابعت ملف صوت/فيديو أو استخدم /to_m4a الأول.")
        return
    tf = await file_obj.get_file()
    in_path  = Path(f"in_{tf.file_unique_id}")
    out_path = Path(f"out_{tf.file_unique_id}.m4a")
    await tf.download_to_drive(in_path)
    try:
        audio = AudioSegment.from_file(in_path)
        audio.export(out_path, format="mp4")  # m4a container (AAC)
        await update.message.reply_audio(audio=out_path.open("rb"), caption="اتفضل .m4a ✅")
    except Exception as e:
        await update.message.reply_text(f"فشل التحويل: {e}\nتأكد إن FFmpeg على PATH.")
    finally:
        try: in_path.unlink(missing_ok=True)
        except: pass
        try: out_path.unlink(missing_ok=True)
        except: pass

# --- Download & convert YouTube audio (keeps original title & sets proper metadata) ---
async def download_and_convert_yt(update: Update, context: ContextTypes.DEFAULT_TYPE, youtube_url: str):
    """Downloads audio from a YouTube URL and sends it back as M4A, keeping the original title
    (caption + Telegram filename) while staying cookie-free.
    """
    await update.message.reply_text("⏳ ببدأ التحميل والتحويل...")

    def _safe_filename(name: str) -> str:
        name = name.replace("/", "-").replace("\\", "-")
        name = re.sub(r"[\n\r\t]", " ", name)
        name = re.sub(r"[:*?\"<>|]", "", name).strip()
        return name or "audio"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        outtmpl = temp_path / "%(title)s.%(ext)s"

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(outtmpl),
            'noplaylist': True,
            'postprocessors': [
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'm4a', 'preferredquality': '192'},
                {'key': 'FFmpegMetadata', 'add_metadata': True},
            ],
            'postprocessor_args': ['-ar', '44100'],
            'prefer_ffmpeg': True,
            'keepvideo': False,
            'quiet': True,
        }

        try:
            def run_ytdlp():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(youtube_url, download=True)
                    base = ydl.prepare_filename(info)
                    m4a_path = Path(base).with_suffix('.m4a')
                    title = info.get('title') or 'Audio'
                    artist = info.get('artist') or info.get('creator') or info.get('uploader') or ''
                    return m4a_path, title, artist

            loop = asyncio.get_event_loop()
            final_path, meta_title, meta_artist = await loop.run_in_executor(None, run_ytdlp)

            with final_path.open('rb') as f:
                await update.message.reply_audio(
                    audio=InputFile(f, filename=f"{_safe_filename(meta_title)}.m4a"),
                    caption=f"✅ {meta_title}",
                    title=meta_title,
                    performer=meta_artist
                )
            await update.message.reply_text("✅ تم التحميل والإرسال بالاسم .")
        except Exception as e:
            log.exception("Error downloading/converting YouTube video:")
            error_msg = f"❌ حدث خطأ أثناء التحميل أو التحويل:\n{e}"
            if "No Media found" in str(e) or "Unsupported URL" in str(e):
                error_msg += "\nقد يكون الرابط غير مدعوم أو لا يحتوي على صوت."
            elif "ffmpeg" in str(e).lower():
                error_msg += "\nتأكد من تثبيت FFmpeg ووجوده في PATH."
            await update.message.reply_text(error_msg)

# ========= Gemini AI (friendlier replies, no markdown) =========

def ai_chat_reply(prompt: str) -> str:
    if not GEMINI_KEY:
        return "شغّلتني من غير مفتاح AI. لو عاوزني أجاوب أفضل، حط GEMINI_KEY في .env."
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return "حصلت مشكلة بسيطة. جرّب تاني."

# ========= Handlers =========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    touch_user(update)
    await update.message.reply_text(
        "اختار من تحت: أغاني أو AI. تقدر تبدّل المصدر بين YouTube و Apple. "
        "لو عاوز تحوّل ملفك لـ m4a استخدم /to_m4a.",
        reply_markup=main_menu(update.effective_user.id if update.effective_user else None)
    )

async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    touch_user(update)
    u = update.effective_user
    if not u:
        await update.message.reply_text("لا أقدر أجيب معلومات المستخدم.")
        return
    if ADMIN_ID and u.id != ADMIN_ID:
        await update.message.reply_text("الأمر /whoami متاح للمالك فقط.")
        return
    await update.message.reply_text(
        f"🆔 Your ID: {u.id}\n👤 Username: @{u.username if u.username else '—'}\n👀 Name: {u.first_name or ''} {u.last_name or ''}"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    touch_user(update)
    if ADMIN_ID and update.effective_user and update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("الإحصائيات للمالك فقط.")
        return
    count = len(USERS)
    lines = [f"👥 Users: {count}"]
    for uid, info in USERS.items():
        handle = ("@" + info.get("username","")) if info.get("username") else "(no username)"
        name = " ".join(filter(None, [info.get("first_name",""), info.get("last_name","")])).strip() or "(no name)"
        lines.append(f"• {uid} — {handle} — {name}")
    await update.message.reply_text("\n".join(lines))

async def on_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    touch_user(update)
    text = (update.message.text or "")
    uid = update.effective_user.id

    if text == "🎵 أغاني":
        user_mode[uid] = "music"
        await update.message.reply_text("تمام. اكتب اسم الأغنية.", reply_markup=main_menu(uid))
    elif text == "🤖 AI Chat":
        user_mode[uid] = "ai"
        await update.message.reply_text("تمام. اكتب سؤالك.", reply_markup=main_menu(uid))
    elif text.startswith("🎯 Source: "):
        src = "youtube" if "YouTube" in text else "apple"
        set_pref(uid, "source", src)
        await update.message.reply_text(f"تم ضبط المصدر: {src.title()}", reply_markup=main_menu(uid))
    elif text.startswith("🌍 Country: "):
        cc = text.split(":")[-1].strip().lower()
        set_pref(uid, "country", cc)
        await update.message.reply_text(f"تم ضبط الدولة: {cc.upper()}", reply_markup=main_menu(uid))
    else:
        await handle_query(update, context)

async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    touch_user(update)
    uid = update.effective_user.id
    text = (update.message.text or "").strip()
    if not text:
        return
    mode = user_mode.get(uid)
    if mode == "ai":
        await update.message.chat.send_action(action="typing")
        await update.message.reply_text(ai_chat_reply(text))
        return

    src = get_pref(uid, "source") or "youtube"
    if src == "youtube":
        await update.message.reply_text(f"ببحث في YouTube عن: {text}...")
        results = yt_api_search(text, max_results=12)
        if not results:
            qurl = "https://www.youtube.com/results?q=" + urllib.parse.quote(text)
            await update.message.reply_text(
                "ملقتش نتائج. جرب البحث اليدوي.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔎 YouTube Search", url=qurl)]])
            )
            return
        for r in results[:5]:
            pretty = norm_song_title(r['title']) or r['title']
            caption = f"• {pretty}" + (f" — {r['channel']}" if r.get('channel') else "")
            await update.message.reply_text(caption, reply_markup=listen_kb_youtube(r["url"], r["title"]))
    else:
        await update.message.reply_text(f"ببحث في Apple عن: {text}...")
        tracks = comprehensive_apple_search(uid, text, limit_each=6)
        if not tracks:
            await update.message.reply_text("ملقتش نتائج. جرب اسم تاني أو أضف اسم الفنان.")
            return
        for t in tracks[:6]:
            await update.message.reply_text(fmt_track_line(t), reply_markup=kb_for_track(t))

async def on_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    touch_user(update)
    q = update.callback_query
    await q.answer()
    data = (q.data or "").split("|")
    try:
        if data[0] == "src":
            src = data[1]
            query = urllib.parse.unquote(data[2])
            await q.edit_message_text(f"تمام. ببحث في {src.title()} عن: {query}")
            class _FakeMsg:
                text = query
                chat = q.message.chat
                async def reply_text(self, *a, **k): return await q.message.reply_text(*a, **k)
            fake_update = Update(update.update_id, message=_FakeMsg())
            if src == "youtube":
                set_pref(q.from_user.id, "source", "youtube")
            else:
                set_pref(q.from_user.id, "source", "apple")
            await handle_query(fake_update, context)
        elif data[0] == "play":
            track_id = int(data[1])
            t = itunes_lookup(track_id)
            if not t or not t.get("previewUrl"):
                await q.message.reply_text("المعاينة مش متاحة للمقطع ده.")
                return
            name = t.get("trackName", "Track")
            artist = t.get("artistName", "")
            cap = f"{name}" + (f" — {artist}" if artist else "")
            await q.message.reply_audio(audio=t["previewUrl"], caption=cap, title=name, performer=artist)
        elif data[0] == "yt_dl":
            if not q.message or not q.message.chat:
                await q.message.reply_text("❌ خطأ: لم يتم العثور على معلومات المحادثة.")
                return
            youtube_url = urllib.parse.unquote(data[1])
            class _FakeUpdate:
                def __init__(self, message, from_user):
                    self.message = message
                    self.effective_user = from_user
            class _FakeMsg:
                def __init__(self, chat):
                    self.chat = chat
                async def reply_text(self, text, *args, **kwargs):
                    return await q.message.reply_text(text, *args, **kwargs)
                async def reply_audio(self, audio, *args, **kwargs):
                    return await q.message.reply_audio(audio, *args, **kwargs)
            fake_msg = _FakeMsg(q.message.chat)
            fake_update = _FakeUpdate(fake_msg, q.from_user)
            await download_and_convert_yt(fake_update, context, youtube_url)
    except Exception as e:
        log.exception("callback error")
        if q and q.message:
            await q.message.reply_text(f"حصل خطأ: {e}")
        else:
            log.error(f"Error processing callback query, could not reply: {e}")

# ========= main =========
if __name__ == "__main__":
    load_users()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("whoami", whoami))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("to_m4a", to_m4a_start))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.AUDIO | filters.VOICE | filters.VIDEO, to_m4a_receive))
    app.add_handler(MessageHandler(filters.Regex("^🎵 أغاني$|^🤖 AI Chat$|^🎯 Source: |^🌍 Country: "), on_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query))
    app.add_handler(CallbackQueryHandler(on_cb))
    print("🔥 البوت شغال دلوقتي ...")
    app.run_polling()
