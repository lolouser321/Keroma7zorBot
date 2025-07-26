import requests
import os

# هنستخدم المفتاح من Variables
GEMINI_KEY = os.environ.get("GEMINI_KEY")

async def ai_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": user_message
                        }
                    ]
                }
            ]
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, json=payload)
        data = response.json()

        if "candidates" in data:
            ai_answer = data["candidates"][0]["content"]["parts"][0]["text"]
            await update.message.reply_text(f"🤖 {ai_answer}")
        else:
            await update.message.reply_text("😔 حصل خطأ في الاتصال بـ Gemini API.")
            print("Gemini API Error:", data)

    except Exception as e:
        await update.message.reply_text("😔 حصل خطأ في الاتصال بـ Gemini API.")
        print("Exception:", e)