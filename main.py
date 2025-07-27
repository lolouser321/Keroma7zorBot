import yt_dlp
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, CallbackQueryHandler, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")  # هجيب التوكن من Variables
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("DEBUG: دخل على start command")
    keyboard = [[InlineKeyboardButton("🎵 تشغيل أغنية", callback_data='play')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔥 اهلا بيك! دوس على الزرار لتشغيل الأغاني.", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    print(f"DEBUG: المستخدم {query.from_user.id} ضغط زرار: {query.data}")
    if query.data == "play":
        user_states[query.from_user.id] = "play"
        await query.message.reply_text("🎤 ابعت اسم الأغنية اللي عايزها:")

async def play_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    print(f"DEBUG: استقبل رسالة من {user_id}: {update.message.text}")
    
    if user_states.get(user_id) != "play":
        await update.message.reply_text("⛔ دوس زرار تشغيل الأغاني الأول يا بطل!")
        return

    song_name = update.message.text
    await update.message.reply_text(f"🎵 جاري البحث عن: {song_name}")
    print(f"DEBUG: جاري البحث عن الأغنية: {song_name}")

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': 'ytsearch',
        'outtmpl': 'song.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        print("DEBUG: بدأ التحميل من yt_dlp")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(song_name, download=True)
            print(f"DEBUG: تم التحميل بنجاح: {info['title']}")
            filename = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
            print(f"DEBUG: اسم الملف بعد التحويل: {filename}")

        print("DEBUG: بيبعت الأغنية للشات")
        await update.message.reply_audio(audio=open(filename, 'rb'))
        os.remove(filename)
        print("DEBUG: تم مسح الملف المؤقت")
    except Exception as e:
        await update.message.reply_text(f"😢 حصل خطأ: {e}")
        print(f"ERROR DEBUG: حصل خطأ كامل:\n{e}")

def main():
    print("DEBUG: بدأ تشغيل البوت")
    if not BOT_TOKEN:
        print("ERROR: مفيش BOT_TOKEN في Variables")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, play_music))

    print("🔥 البوت شغال... جرب /start")
    app.run_polling()

if __name__ == "__main__":
    main()