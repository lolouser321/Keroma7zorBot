# الصورة الأساسية Python 3.13# الصورة الأساسية Python
FROM python:3.11-slim

# تثبيت ffmpeg (مهم لتشغيل الأغاني)
RUN apt-get update && apt-get install -y ffmpeg

# إنشاء مجلد التطبيق
WORKDIR /app

# نسخ كل الملفات داخل الحاوية
COPY . /app

# تثبيت المكتبات المطلوبة
RUN pip install --no-cache-dir -r requirements.txt

# تشغيل البوت
CMD ["python", "main.py"]