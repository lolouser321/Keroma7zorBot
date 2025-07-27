import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, ChatMemberHandler, filters
)
from yt_dlp import YoutubeDL
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN", "ضع_التوكن_هنا")
GEMINI_KEY = os.environ.get("GEMINI_KEY", "ضع_API_هنا")

# اختيار الوضع الحالي (افتراضي: تلقائي)
user_modes = {}

# ========== Gemini AI ==========
def ask_gemini(prompt):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        headers = {"Content-Type": "application/json"}
        r = requests.post(url, json=payload, headers=headers).json()
        return r["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "😅 مش قادر أرد دلوقتي."

# ========== زرار اختيار الوضع ==========
async def mode_selector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎵 وضع الموسيقى", callback_data='music')],
        [InlineKeyboardButton("🤖 وضع كيرو-AI", callback_data='ai')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚡ اختار الوضع اللي تحبه:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == 'music':
        user_modes[user_id] = "music"
        await query.message.reply_text("🎵 دخلت وضع تشغيل الأغاني! اكتب اسم الأغنية علطول.")
    elif query.data == 'ai':
        user_modes[user_id] = "ai"
        await query.message.reply_text("🤖 دخلت وضع كيرو-AI! اسألني أي سؤال.")

# ========== التعامل مع الرسائل ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    # لو المستخدم اختار وضع موسيقى
    if user_modes.get(user_id) == "music":
        return await play_music(update, text)

    # لو المستخدم اختار وضع AI
    if user_modes.get(user_id) == "ai":
        return await update.message.reply_text(f"🤖 {ask_gemini(text)}")

    # لو الوضع التلقائي: نحلل النص
    if re.search(r"(شغل|اغنية|أغنية|أغني|اسمع)", text):
        return await play_music(update, text)

    # الافتراضي AI
    return await update.message.reply_text(f"🤖 {ask_gemini(text)}")

# ========== تشغيل الموسيقى ==========
async def play_music(update: Update, query: str):
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
        await update.message.reply_text("❌ حصل خطأ أثناء تحميل الأغنية. يمكن تحتاج Cookies.")

# ========== ترحيب الأعضاء الجدد ==========
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        welcome_msg = f"""
🌟🎉 أهلاً وسهلاً يا {member.first_name}! 🎉🌟

🔥 نورت الجروب!  
💡 تقدر تقول للبوت مباشرة: "شغل اغنية محمد رمضان" أو اسأل أي حاجة في أي وقت.  
👇 دوس على الزرار لاختيار وضعك المفضل:
"""
        keyboard = [
            [InlineKeyboardButton("🎵 وضع الموسيقى", callback_data='music')],
            [InlineKeyboardButton("🤖 وضع كيرو-AI", callback_data='ai')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_msg, reply_markup=reply_markup)

# ========== MAIN ==========
def main():
    print("🔥 البوت شغال بدون أوامر، اكتب بس اللي عايزه!")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("mode", mode_selector))  # تغيير الوضع بأي وقت
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(ChatMemberHandler(welcome, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
