[13.09.2026 1:28] Odil: import os
import json
import base64
import threading
from pathlib import Path

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI

BOT_TOKEN = os.environ["BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(name)


@app.get("/")
def home():
    return "Uzum AutoCard Bot is running."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📸 Tovar rasmi yuborish", callback_data="new")]
    ]

    await update.message.reply_text(
        "🚗 Uzum AutoCard botiga xush kelibsiz!\n\n"
        "Mahsulot rasmini yuboring — men nom, SEO tavsif, "
        "mos avtomobillar va kalit so‘zlarni tayyorlayman.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "📸 Mahsulot rasmini yuboring."
    )


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = await update.message.reply_text(
        "🔎 Mahsulot tahlil qilinmoqda..."
    )

    telegram_file = await update.message.photo[-1].get_file()

    path = Path("/tmp") / f"autocard_{update.effective_user.id}.jpg"

    await telegram_file.download_to_drive(path)

    image_data = base64.b64encode(path.read_bytes()).decode()

    prompt = """
Siz Uzum marketplace uchun avtomobil ehtiyot qismlari SEO mutaxassisisisiz.

Rasmni tahlil qiling.
Rasmda ko‘rinmagan ma'lumotni uydirmang.

JSON formatida javob bering:

{
"title_uz":"",
"title_ru":"",
"category":"",
"brand":"",
"oem":"",
"compatibility":"",
"description_uz":"",
"description_ru":"",
"keywords":"",
"benefits":["","","","",""]
}
"""

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt,
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{image_data}",
                        },
                    ],
                }
            ],
        )

        text = response.output_text

        start_index = text.find("{")
        end_index = text.rfind("}")

        data = json.loads(
            text[start_index:end_index + 1]
        )

        benefits = "\n".join(
            "✅ " + item
            for item in data.get("benefits", [])
            if item
        )

        result = (
            "🛒 <b>UZUM TOVAR KARTOCHKASI</b>\n\n"
            f"<b>🇺🇿 Nomi:</b> {data.get('title_uz', '')}\n"
            f"<b>🇷🇺 Название:</b> {data.get('title_ru', '')}\n"
            f"<b>📂 Kategoriya:</b> {data.get('category', '')}\n"
            f"<b>🏷 Brend:</b> {data.get('brand', '')}\n"
            f"<b>🔢 OEM:</b> {data.get('oem', '')}\n"
            f"<b>🚗 Mosligi:</b> {data.get('compatibility', '')}\n\n"
            f"<b>🇺🇿 Tavsif:</b>\n"
            f"{data.get('description_uz', '')}\n\n"
            f"<b>🇷🇺 Описание:</b>\n"
            f"{data.get('description_ru', '')}\n\n"
            f"<b>🔑 Kalit so‘zlar:</b>\n"
            f"{data.get('keywords', '')}\n\n"
            f"<b>⭐ Afzalliklar:</b>\n"
            f"{benefits}"
        )

        await message.edit_text(
            result,
            parse_mode="HTML",
        )

    except Exception as error:
        print("ERROR:", repr(error))

        await message.edit_text(
            "❌ Xatolik yuz berdi. Render Logs bo‘limini tekshiring."
        )


def run_web_server():
    port = int(os.environ.get("PORT", "10000"))
[13.09.2026 1:28] Odil: app.run(
        host="0.0.0.0",
        port=port,
    )


def main():
    threading.Thread(
        target=run_web_server,
        daemon=True,
    ).start()

    bot = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    bot.add_handler(
        CommandHandler("start", start)
    )

    bot.add_handler(
        CallbackQueryHandler(button)
    )

    bot.add_handler(
        MessageHandler(filters.PHOTO, photo)
    )

    bot.run_polling()


if name == "main":
    main()
