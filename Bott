import telebot

TOKEN = "8340842896:AAFvMaI1g-2kIzRJA-BoLz9qssP5fLGnt00"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "أهلا بيك في بوت Keroma7zor_bot 😎\nابعت أي حاجة وأنا هرد عليك!")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"إنت كتبت: {message.text}")

bot.infinity_polling()
