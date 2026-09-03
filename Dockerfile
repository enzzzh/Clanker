FROM python:3.11-slim

WORKDIR /app

# ⚡ Install FFmpeg AND NodeJS (the JS interpreter) cleanly
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    ffmpeg \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["python", "bot.py"]
