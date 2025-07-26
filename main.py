import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, 
    CallbackContext, CallbackQueryHandler
)
import openai
import requests
import json
from dotenv import load_dotenv

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إعداد OpenAI
openai.api_key = "YOUR_OPENAI_API_KEY"  # ضع مفتاح API الخاص بك

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

# رسالة المساعدة
HELP_MESSAGE = """
🤖 أوامر البوت:

🎵 تشغيل الأغاني:
اكتب: أغنية عمرو دياب بابا
او: شغل أغانى محمد منير

❓ الأسئلة والاستفسارات:
اكتب سؤالك مباشرة وانا هرد عليك بالمصري

🔊 فك الميوت:
اضغط على الزر أدناه عشان تفك الميوت من القناة

🔗 رابط القناة: {}
""".format(CHANNEL_USERNAME)

def start(update: Update, context: CallbackContext) -> None:
    """رسالة البداية"""
    keyboard = [
        [InlineKeyboardButton("🔊 فك الميوت من القناة", callback_data='unmute')],
        [InlineKeyboardButton("🎵 تشغيل أغنية", callback_data='play_song')],
        [InlineKeyboardButton("❓ المساعدة", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(WELCOME_MESSAGE, reply_markup=reply_markup)

def unmute_instructions(update: Update, context: CallbackContext) -> None:
    """تعليمات فك الميوت"""
    instructions = """
🔊 طريقة فك الميوت من القناة:

1️⃣ ادخل لقناة @strongest_live_tiktok
2️⃣ اضغط على اسم القناة في أعلى الشاشة
3️⃣ ابحث عن زر "التنبيهات" أو "Notifications"
4️⃣ اضغط عليه وابحث عن "إلغاء الكتم" أو "Unmute"
5️⃣ اضغط على "تم" أو "Done"

✅ بعد ما تكمل الخطوات دي، ارجع هنا واكتب:
/check_mute للتأكد من إنك فككت الميوت

📌 ملحوظة: ممكن تاخد دقيقة أو اتنين عشان التحديث يحصل
"""
    update.message.reply_text(instructions)

def check_mute_status(update: Update, context: CallbackContext) -> None:
    """التحقق من حالة الميوت"""
    update.message.reply_text("⚠️ ملحوظة: البوت مش ممكن يتأكد من حالة الميوت تلقائيًا.\n\nتأكد بنفسك من إنك فككت الميوت من القناة @strongest_live_tiktok")

def help_command(update: Update, context: CallbackContext) -> None:
    """أمر المساعدة"""
    keyboard = [
        [InlineKeyboardButton("🔊 فك الميوت", callback_data='unmute')],
        [InlineKeyboardButton("🎵 تشغيل أغاني", callback_data='play_song')],
        [InlineKeyboardButton("🤖 الذكاء الاصطناعي", callback_data='ai_help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(HELP_MESSAGE, reply_markup=reply_markup)

def ai_response(update: Update, context: CallbackContext) -> None:
    """الرد باستخدام الذكاء الاصطناعي"""
    user_message = update.message.text
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي لمجموعة تيليجرام. ردا بالمصري العامي بطريقة ودودة ومفيدة. أجب باللغة العربية فقط."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        ai_answer = response.choices[0].message.content
        update.message.reply_text(f"🤖 {ai_answer}")
        
    except Exception as e:
        logger.error(f"Error in AI response: {e}")
        update.message.reply_text("😔 عذراً، حصل خطأ في الاتصال بالذكاء الاصطناعي. جرب تاني كده.")

def play_song(update: Update, context: CallbackContext) -> None:
    """تشغيل الأغاني"""
    user_message = update.message.text.lower()
    
    # البحث عن كلمات تدل على طلب أغنية
    song_keywords = ['أغنية', 'شغل', 'أغنيه', 'تشغيل', 'عمرو دياب', 'محمد منير', 'بابا', 'أغاني']
    
    if any(keyword in user_message for keyword in song_keywords):
        # استخراج اسم الأغنية
        song_name = extract_song_name(user_message)
        
        if song_name:
            search_message = f"🎵 ببحث عن: {song_name}\n\n⚠️ ملحوظة: لأسباب قانونية، البوت مش ممكن يشغل الأغاني مباشرة، لكن ممكن تستخدم تطبيقات زي:\n• Spotify\n• YouTube Music\n• Anghami\n• Deezer"
            
            update.message.reply_text(search_message)
        else:
            update.message.reply_text("🎵 اكتب اسم الأغنية اللي عايز تشغلها، مثلاً:\n'أغنية عمرو دياب بابا'\n'شغل محمد منير'")
    else:
        # إذا كانت الرسالة عادية، نرسلها للذكاء الاصطناعي
        ai_response(update, context)

def extract_song_name(message: str) -> str:
    """استخراج اسم الأغنية من الرسالة"""
    # إزالة الكلمات المفتاحية
    keywords_to_remove = ['أغنية', 'شغل', 'أغنيه', 'تشغيل']
    
    song_name = message
    for keyword in keywords_to_remove:
        song_name = song_name.replace(keyword, '')
    
    song_name = song_name.strip()
    
    return song_name if song_name else None

def button_handler(update: Update, context: CallbackContext) -> None:
    """معالجة الضغط على الأزرار"""
    query = update.callback_query
    query.answer()
    
    if query.data == 'unmute':
        unmute_instructions(update, context)
    elif query.data == 'play_song':
        query.message.reply_text("🎵 اكتب اسم الأغنية اللي عايز تشغلها، مثلاً:\n'أغنية عمرو دياب بابا'")
    elif query.data == 'help':
        help_command(update, context)
    elif query.data == 'ai_help':
        query.message.reply_text("🤖 اسألني أي سؤال وهرد عليك بالمصري!\nمثلاً: 'أيه أجمل أغاني عمرو دياب؟'")

def new_member(update: Update, context: CallbackContext) -> None:
    """رسالة الترحيب للأعضاء الجدد"""
    for member in update.message.new_chat_members:
        welcome_text = f"""
🎉 مرحباً {member.first_name}! 

🎵 مرحباً بيك في قناتنا الرسمية Strongest Live TikTok!

🔊 عشان تستمتع بالمحتوى:
1️⃣ اتأكد إنك فككت الميوت من القناة
2️⃣ استخدم البوت عشان تشغل الأغاني أو تسأل أسئلة
3️⃣ اكتب /start في البوت عشان تعرف كل المميزات

🤖 البوت: @اسم_البوت_بتاعك
🔗 القناة: {CHANNEL_USERNAME}
"""
        
        keyboard = [
            [InlineKeyboardButton("🔊 فك الميوت", callback_data='unmute')],
            [InlineKeyboardButton("🎵 تشغيل أغنية", callback_data='play_song')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(welcome_text, reply_markup=reply_markup)

def main() -> None:
    """الدالة الرئيسية"""
    # ضع التوكن بتاع البوت هنا
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # الأوامر
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("unmute", unmute_instructions))
    dispatcher.add_handler(CommandHandler("check_mute", check_mute_status))

    # رسائل الأعضاء الجدد
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_member))

    # الرسائل النصية
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, play_song))

    # الأزرار
    dispatcher.add_handler(CallbackQueryHandler(button_handler))

    # بدء البوت
    updater.start_polling()
    logger.info("البوت اشتغل!")
    updater.idle()

if __name__ == '__main__':
    main()