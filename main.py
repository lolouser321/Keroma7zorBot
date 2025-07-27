import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters

# جلب التوكن من الـ Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎵 تشغيل أغنية", callback_data="play_song")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔥 أهلاً بيك! دوس على الزرار لتشغيل الأغاني.", reply_markup=reply_markup)

# زرار التشغيل
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "play_song":
        await query.edit_message_text("🎤 ابعت اسم الأغنية اللي عايزها:")

# تشغيل الأغنية
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    song_name = update.message.text
    await update.message.reply_text(f"🎵 جاري البحث عن: {song_name}")

    try:
        ydl_opts = {'format': 'bestaudio', 'outtmpl': 'song.%(ext)s'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{song_name}", download=True)['entries'][0]
            file_path = ydl.prepare_filename(info)
            await update.message.reply_audio(audio=open(file_path, 'rb'), title=info['title'])
    except Exception as e:
        await update.message.reply_text("😢 حصل خطأ أثناء تشغيل الأغنية")
        print("Error:", e)

def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN مش موجود في Environment Variables!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🔥 البوت شغال... جرب /start")
    app.run_polling()

if __name__ == "__main__":
    main()
