# الصورة الأساسية Python 3.13
FROM python:3.13-slim

# تثبيت ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# مجلد التطبيق
WORKDIR /app

# نسخ كل الملفات إلى داخل الحاوية
COPY . /app

# تثبيت المكتبات المطلوبة
RUN pip install --no-cache-dir -r requirements.txt

# تشغيل البوت
CMD ["python", "main.py"]