import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# تشغيل اللوجز عشان يظهر في Railway
logging.basicConfig(level=logging.INFO)

# التوكن من الـ Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 البوت شغال تمام من Railway!")

if __name__ == '__main__':
    if BOT_TOKEN is None:
        print("⛔ BOT_TOKEN مش موجود في Variables على Railway!")
    else:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        print("🚀 البوت شغال... جرب /start")
        app.run_polling()