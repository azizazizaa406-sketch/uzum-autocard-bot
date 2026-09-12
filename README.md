# Uzum AutoCard Telegram Bot

## 1. Telegram bot ochish
Telegramda @BotFather ni oching -> /newbot -> bot nomi va username bering.
Olingan tokenni `.env` faylidagi `BOT_TOKEN` ga yozing.

## 2. OpenAI API key
OpenAI API kalitini `.env` faylidagi `OPENAI_API_KEY` ga yozing.

## 3. O‘rnatish
```bash
pip install -r requirements.txt
```

## 4. Ishga tushirish

Linux/macOS:
```bash
export BOT_TOKEN="..."
export OPENAI_API_KEY="..."
python bot.py
```

Windows PowerShell:
```powershell
$env:BOT_TOKEN="..."
$env:OPENAI_API_KEY="..."
python bot.py
```

Botga `/start` yuboring va mahsulot rasmini yuboring.

## Keyingi modul
1080x1440 professional infografika generatorini alohida modul sifatida ulash mumkin.
