import os
import telebot
import requests
from yt_dlp import YoutubeDL

# ====== جلب القيم السرية من Environment Variables ======
TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_KEY")
CHANNEL_ID = os.environ.get("CHANNEL_ID")  # ممكن تضيفه في المتغيرات لو هتربط القناة

bot = telebot.TeleBot(TOKEN)

# ====== Banner الترحيب ======
BANNER_URL = "https://i.ibb.co/QDQSLpH/banner.png"  # الصورة الترحيبية

@bot.chat_member_handler()
def welcome_new_user(message: telebot.types.ChatMemberUpdated):
    if message.new_chat_member and message.new_chat_member.status == "member":
        user_name = message.new_chat_member.user.first_name
        bot.send_photo(
            message.chat.id,
            BANNER_URL,
            caption=(
                f"أهلا بيك يا {user_name} في قناة strongest live tiktok 🌟\n"
                "متنساش تشيل الميوت من على القناة لو معمول 🔔\n\n"
                "علشان تتأكد إن الميوت مش شغال:\n"
                "1️⃣ افتح القناة\n"
                "2️⃣ دوس على اسم القناة فوق\n"
                "3️⃣ شوف علامة الجرس 🔔 لو عليه خط، شيله\n\n"
                "استمتع معانا 🎉"
            )
        )

# ====== ذكاء اصطناعي (OpenAI GPT) ======
def ask_gpt(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "انت مساعد شقي وبترد بالمصري الشعبي."},
            {"role": "user", "content": prompt}
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]

@bot.message_handler(commands=['ask'])
def ai_reply(message):
    question = message.text.replace("/ask", "").strip()
    if not question:
        bot.reply_to(message, "اكتب السؤال بعد الأمر /ask يا معلم 🤖")
    else:
        bot.reply_to(message, "ثانية بس يا نجم بفكر 🤔...")
        answer = ask_gpt(question)
        bot.send_message(message.chat.id, answer)

# ====== تشغيل أغاني من يوتيوب ======
@bot.message_handler(commands=['play'])
def play_song(message):
    query = message.text.replace("/play", "").strip()
    if query:
        bot.reply_to(message, f"بدور على الأغنية: {query} 🎵")
        ydl_opts = {'format': 'bestaudio', 'outtmpl': 'song.%(ext)s'}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=True)['entries'][0]
            file_path = ydl.prepare_filename(info)
            bot.send_audio(message.chat.id, open(file_path, 'rb'))
    else:
        bot.reply_to(message, "اكتب اسم الأغنية بعد الأمر /play يا نجم 🎧")

# ====== أزرار رئيسية ======
@bot.message_handler(commands=['start'])
def send_welcome(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("🤖 اسأل سؤال", "🎵 شغل أغنية")
    bot.send_message(message.chat.id, "أهلا بيك في بوت strongest live tiktok 🔥", reply_markup=keyboard)

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    if message.text == "🤖 اسأل سؤال":
        bot.reply_to(message, "ابعت سؤالك كده مع الأمر /ask 🤖")
    elif message.text == "🎵 شغل أغنية":
        bot.reply_to(message, "اكتب اسم الأغنية مع الأمر /play 🎵")
    else:
        bot.reply_to(message, "ممكن تستخدم الأزرار أو تكتب أوامر /ask و /play.")

bot.infinity_polling()