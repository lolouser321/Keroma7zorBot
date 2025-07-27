import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from yt_dlp import YoutubeDL

BOT_TOKEN = os.environ.get("BOT_TOKEN", "حط_التوكن_هنا")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    if any(word in query for word in ["شغل", "اغنية", "أغنية", "شغلي"]):
        await update.message.reply_text(f"🎵 بحمّل: {query}")
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': '%(title)s.%(ext)s',
                'noplaylist': True,
                'quiet': False,
                'cookiefile': 'youtube.com_cookies.txt' if os.path.exists('youtube.com_cookies.txt') else None
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=True)['entries'][0]
                file_path = ydl.prepare_filename(info)

            with open(file_path, 'rb') as song:
                await update.message.reply_audio(audio=song, title=info['title'])

            os.remove(file_path)

        except Exception as e:
            print(f"❌ Error: {e}")
            await update.message.reply_text("❌ حصل خطأ أثناء تحميل الأغنية. يمكن لازم Cookies.")
    else:
        await update.message.reply_text("🤖 اكتب اسم أغنية تبدأ بـ شغل ...")

def main():
    print("🔥 البوت شغال زي النسخة القديمة")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
