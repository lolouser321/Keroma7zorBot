import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CallbackQueryHandler,
    ContextTypes, ChatMemberHandler, filters
)
from yt_dlp import YoutubeDL
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN", "ضع_التوكن_هنا")
GEMINI_KEY = os.environ.get("GEMINI_KEY", "ضع_API_هنا")

# تتبع وضع المستخدم
play_mode_users = set()

# ====== ذكاء اصطناعي Gemini ======
def ask_gemini(prompt):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        headers = {"Content-Type": "application/json"}
        r = requests.post(url, json=payload, headers=headers).json()
        return r["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "😅 مش قادر أرد دلوقتي، جرب تاني!"

# ====== تشغيل الأغاني ======
async def play_song(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
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
        print("🗑️ تم مسح الملف")

    except Exception as e:
        print(f"❌ Error: {e}")
        await update.message.reply_text("❌ حصل خطأ أثناء تحميل الأغنية. يمكن تحتاج Cookies.")

# ====== التعامل مع الرسائل ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    # لو المستخدم في وضع تشغيل الأغاني بالفعل
    if user_id in play_mode_users:
        play_mode_users.remove(user_id)
        return await play_song(update, context, text)

    # لو الرسالة فيها كلمة شغل أو اغنية → شغل أغنية مباشرة
    if re.search(r"(شغل|اغنية|أغنية|أغني|اسمع)", text):
        return await play_song(update, context, text)

    # غير كده رد بالذكاء الاصطناعي
    response = ask_gemini(text)
    return await update.message.reply_text(f"🤖 {response}")

# ====== ترحيب بالأعضاء الجدد ======
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        welcome_text = f"""
🌟🎉 أهلاً يا {member.first_name}! 🎉🌟
🔥 نورت الجروب، اكتب أي حاجة وأنا معاك:
- قول "شغل اغنية" وشوف السحر 🎵
- اسألني أي سؤال وهرُد عليك 🤖
"""
        await update.message.reply_text(welcome_text)

# ====== Main ======
def main():
    print("🔥 البوت شغال على طول، مش محتاج /start")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ترحيب
    app.add_handler(ChatMemberHandler(welcome, ChatMemberHandler.CHAT_MEMBER))

    # التعامل مع كل الرسائل النصية
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
