# نستخدم نسخة Python خفيفة
FROM python:3.11-slim

# تثبيت ffmpeg عشان الصوتيات
RUN apt-get update && apt-get install -y ffmpeg

# نحدد مكان التطبيق
WORKDIR /app

# نسخ كل الملفات للفولدر
COPY . /app

# تثبيت المكتبات
RUN pip install --no-cache-dir -r requirements.txt

# تشغيل البوت
CMD ["python", "main.py"]