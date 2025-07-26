import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from yt_dlp import YoutubeDL


# خد التوكن من Railway Variables (أو حطه هنا لو محلي)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ضع_التوكن_لو_محلي")

# نخزن مين اللي داخل وضع تشغيل الأغاني
play_mode_users = set()

# ========== /start ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎵 شغل أغنية", callback_data='play_mode')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎉 أهلاً بيك! اضغط زر تشغيل الأغاني:", reply_markup=reply_markup)

# ========== تشغيل الأغاني ==========
async def play_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # لو المستخدم مش في وضع الأغاني يتجاهل الرسالة
    if user_id not in play_mode_users:
        return  

    query = update.message.text
    play_mode_users.remove(user_id)

    await update.message.reply_text(f"🎵 بحمّل: {query}")
    try:
        # ffmpeg في Railway هيتسطب جوه الـ Docker
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'noplaylist': True,
            'quiet': True
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=True)['entries'][0]
            file_path = ydl.prepare_filename(info)

        # إرسال الملف الصوتي
        with open(file_path, 'rb') as song:
            await update.message.reply_audio(audio=song, title=info['title'])

        # حذف الملف بعد الإرسال
        os.remove(file_path)

    except Exception as e:
        await update.message.reply_text("❌ حصل خطأ أثناء تحميل الأغنية.")
        print("Error:", e)

# ========== الأزرار ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == 'play_mode':
        play_mode_users.add(user_id)
        await query.message.reply_text("🎵 اكتب اسم الأغنية اللي عايز تشغلها:")

# ========== تشغيل البوت ==========
def main():
    print("🔥 البوت شغال... جرب /start")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, play_song))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()