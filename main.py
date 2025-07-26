import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, CallbackQueryHandler, filters
)
import openai
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# قراءة المفاتيح من الـ Environment Variables
openai.api_key = os.environ.get("OPENAI_KEY")
TOKEN = os.environ.get("BOT_TOKEN")

# اسم القناة
CHANNEL_USERNAME = "@strongest_live_tiktok"

# رسالة الترحيب
WELCOME_MESSAGE = """
🎉 مرحباً بيك في قناتنا الرسمية!

🎵 قناة Strongest Live TikTok
🔥 أقوى محتوى تيك توك مباشر

📌 خطوات فك الميوت:
1. اضغط على "🔊 فك الميوت"
2. اتبع التعليمات اللي هتظهرلك
3. تأكد من إنك مش ميوت من القناة

🎯 مميزات البوت:
• 🤖 ذكاء اصطناعي للإجابة على الأسئلة
• 🎵 تشغيل الأغاني مباشرة
• 💬 مساعدة فورية

لطلب المساعدة اكتب: /help
"""

HELP_MESSAGE = f"""
🤖 أوامر البوت:

🎵 تشغيل الأغاني:
اكتب: أغنية عمرو دياب بابا
او: شغل أغانى محمد منير

❓ الأسئلة والاستفسارات:
اكتب سؤالك مباشرة وانا هرد عليك بالمصري

🔊 فك الميوت:
اضغط على الزر أدناه عشان تفك الميوت من القناة

🔗 رابط القناة: {CHANNEL_USERNAME}
"""

# =================== الأوامر ===================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔊 فك الميوت من القناة", callback_data='unmute')],
        [InlineKeyboardButton("🎵 تشغيل أغنية", callback_data='play_song')],
        [InlineKeyboardButton("❓ المساعدة", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(WELCOME_MESSAGE, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔊 فك الميوت", callback_data='unmute')],
        [InlineKeyboardButton("🎵 تشغيل أغاني", callback_data='play_song')],
        [InlineKeyboardButton("🤖 الذكاء الاصطناعي", callback_data='ai_help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(HELP_MESSAGE, reply_markup=reply_markup)

async def unmute_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    instructions = """
🔊 طريقة فك الميوت من القناة:

1️⃣ ادخل لقناة @strongest_live_tiktok
2️⃣ اضغط على اسم القناة في أعلى الشاشة
3️⃣ ابحث عن زر "التنبيهات" أو "Notifications"
4️⃣ اضغط عليه وابحث عن "إلغاء الكتم" أو "Unmute"
5️⃣ اضغط على "تم" أو "Done"

✅ بعد ما تكمل الخطوات دي، ارجع هنا واكتب:
/check_mute للتأكد من إنك فككت الميوت
"""
    await update.message.reply_text(instructions)

async def check_mute_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚠️ ملحوظة: البوت مش ممكن يتأكد من حالة الميوت تلقائيًا.\n\n"
        "تأكد بنفسك من إنك فككت الميوت من القناة @strongest_live_tiktok"
    )

async def ai_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي بترد بالمصري."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        ai_answer = response.choices[0].message.content
        await update.message.reply_text(f"🤖 {ai_answer}")
    except Exception as e:
        logger.error(f"Error in AI response: {e}")
        await update.message.reply_text("😔 حصل خطأ في الاتصال بالذكاء الاصطناعي. جرب تاني.")

async def play_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()
    keywords = ['أغنية', 'شغل', 'أغنيه', 'تشغيل', 'عمرو دياب', 'محمد منير', 'بابا', 'أغاني']
    if any(keyword in user_message for keyword in keywords):
        song_name = extract_song_name(user_message)
        if song_name:
            await update.message.reply_text(
                f"🎵 ببحث عن: {song_name}\n\n⚠️ مفيش تشغيل مباشر دلوقتي، استخدم تطبيقات زي:\n• Spotify\n• YouTube Music\n• Anghami"
            )
        else:
            await update.message.reply_text("🎵 اكتب اسم الأغنية اللي عايز تشغلها.")
    else:
        await ai_response(update, context)

def extract_song_name(message: str) -> str:
    keywords_to_remove = ['أغنية', 'شغل', 'أغنيه', 'تشغيل']
    for keyword in keywords_to_remove:
        message = message.replace(keyword, '')
    return message.strip()

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'unmute':
        await unmute_instructions(update, context)
    elif query.data == 'play_song':
        await query.message.reply_text("🎵 اكتب اسم الأغنية اللي عايز تشغلها.")
    elif query.data == 'help':
        await help_command(update, context)
    elif query.data == 'ai_help':
        await query.message.reply_text("🤖 اسأل أي سؤال وهرد عليك بالمصري.")

async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        welcome_text = f"""
🎉 مرحباً {member.first_name}! 

🎵 مرحباً بيك في قناة Strongest Live TikTok!

🔊 اتأكد إنك فككت الميوت من القناة
🤖 استخدم البوت عشان تسأل أو تشغل أغاني
"""
        keyboard = [
            [InlineKeyboardButton("🔊 فك الميوت", callback_data='unmute')],
            [InlineKeyboardButton("🎵 تشغيل أغنية", callback_data='play_song')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# =================== التشغيل ===================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("unmute", unmute_instructions))
    app.add_handler(CommandHandler("check_mute", check_mute_status))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, play_song))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("البوت اشتغل!")
    app.run_polling()

if __name__ == '__main__':
    main()