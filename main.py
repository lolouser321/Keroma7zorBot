import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, ChatMemberHandler, filters
)
from yt_dlp import YoutubeDL
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN", "ضع_التوكن_هنا_لو_محلي")
GEMINI_KEY = os.environ.get("GEMINI_KEY", "ضع_مفتاح_API_لو_محلي")

play_mode_users = set()

# ==== ذكاء اصطناعي (Gemini API) ====
def ask_gemini(prompt):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        headers = {"Content-Type": "application/json"}
        r = requests.post(url, json=payload, headers=headers).json()
        return r["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return "😅 مش قادر أرد دلوقتي."

# ==== زرار /start ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎵 شغل أغنية", callback_data='play_mode')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎉 أهلاً بيك! اضغط زر تشغيل الأغاني:", reply_markup=reply_markup)

# ==== تشغيل الأغاني ====
async def play_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in play_mode_users:
        # لو مش في وضع الأغاني، خلي الرسالة للذكاء الاصطناعي
        question = update.message.text
        answer = ask_gemini(question)
        await update.message.reply_text(f"🤖 {answer}")
        return  

    query = update.message.text
    play_mode_users.remove(user_id)
    await update.message.reply_text(f"🎵 بحمّل: {query}")

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'noplaylist': True,
            'quiet': False
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=True)['entries'][0]
            file_path = ydl.prepare_filename(info)

        with open(file_path, 'rb') as song:
            await update.message.reply_audio(audio=song, title=info['title'])

        os.remove(file_path)

    except Exception as e:
        print(f"❌ Error: {e}")
        await update.message.reply_text("❌ حصل خطأ أثناء تحميل الأغنية.")

# ==== زرار تشغيل الأغاني ====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == 'play_mode':
        play_mode_users.add(user_id)
        await query.message.reply_text("🎵 اكتب اسم الأغنية اللي عايز تشغلها:")

# ==== ترحيب بالأعضاء الجدد ====
async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        welcome_text = f"""
🎉 أهلاً بيك يا {member.first_name} في الجروب!
📌 متنساش تشيل الميوت عشان توصلك كل حاجة.

اكتب /start وجرب زرار الأغاني أو اسأل أي سؤال 👌
"""
        await update.message.reply_text(welcome_text)

# ==== Main ====
def main():
    print("🔥 البوت شغال... جرب /start")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(ChatMemberHandler(new_member, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, play_song))

    app.run_polling()

if __name__ == "__main__":
    main()
