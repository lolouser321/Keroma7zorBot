import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from yt_dlp import YoutubeDL

BOT_TOKEN = os.environ.get("BOT_TOKEN", "حط_التوكن_هنا")

play_mode_users = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📢 /start command received")  # Debug
    keyboard = [[InlineKeyboardButton("🎵 شغل أغنية", callback_data='play_mode')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎉 أهلاً بيك! اضغط زر تشغيل الأغاني:", reply_markup=reply_markup)

async def play_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    print(f"📢 رسالة جديدة من {user_id}: {update.message.text}")  # Debug

    # لازم يدخل وضع التشغيل الأول
    if user_id not in play_mode_users:
        print("⛔ المستخدم مش في وضع تشغيل الأغاني")
        return  

    query = update.message.text
    play_mode_users.remove(user_id)

    await update.message.reply_text(f"🎵 بحمّل: {query}")
    try:
        ffmpeg_path = os.path.join(os.getcwd(), "bin")
        print(f"📂 ffmpeg path: {ffmpeg_path}")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'noplaylist': True,
            'quiet': False,  # Debug 
            'ffmpeg_location': ffmpeg_path,
            'cookiefile': 'youtube.com_cookies.txt' if os.path.exists('youtube.com_cookies.txt') else None
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=True)['entries'][0]
            file_path = ydl.prepare_filename(info)
            print(f"✅ تم التحميل: {file_path}")

        with open(file_path, 'rb') as song:
            await update.message.reply_audio(audio=song, title=info['title'])

        os.remove(file_path)
        print("🗑️ تم مسح الملف بعد الإرسال")

    except Exception as e:
        print(f"❌ Error: {e}")
        await update.message.reply_text("❌ حصل خطأ أثناء تحميل الأغنية. يمكن محتاج Cookies.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    print(f"📢 الزرار اتضغط من {user_id}")

    if query.data == 'play_mode':
        play_mode_users.add(user_id)
        await query.message.reply_text("🎵 اكتب اسم الأغنية اللي عايز تشغلها:")

def main():
    print("🔥 البوت شغال... جرب /start")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, play_song))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
