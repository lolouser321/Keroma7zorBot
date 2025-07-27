FROM python:3.11-slim

# تثبيت ffmpeg (لازم للأغاني)
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
