import os
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

app = Flask(__name__)


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
    try:
        await update.callback_query.answer()
    except Exception:
        pass

    if update.callback_query.data == "infographic":
        await update.callback_query.message.reply_text(
            "🎨 Infografika tayyorlanmoqda...\n\n"
            "⏳ Bir oz kuting."
        )

        try:
            image_path = context.user_data.get("image_path")

            if not image_path:
                await update.callback_query.message.reply_text(
                    "❌ Mahsulot rasmi topilmadi. Rasmni qayta yuboring."
                )
                return

            result = client.images.edit(
                model="gpt-image-2",
                image=open(image_path, "rb"),
                prompt="""
Create a premium automotive marketplace product image.

IMPORTANT:
- Preserve the exact product from the reference image.
- Do not change the product shape, construction, holes, mounting points,
  dimensions, labels or visible details.
- Remove the original background.
- Put the product on a clean #EFEFEF light gray background.
- Product centered and large.
- Professional studio lighting.
- Realistic shadows and reflections.
- Premium Korean automotive parts advertising style.
- Clean commercial product photography.
- Vertical marketplace composition.
- NO text.
- NO logos.
- NO watermark.
""",
                size="1024x1536",
                quality="medium",
            )

            image_bytes = base64.b64decode(result.data[0].b64_json)

            from io import BytesIO

            await update.callback_query.message.reply_photo(
                photo=BytesIO(image_bytes),
                caption="🎨 Premium infografika tayyor!"
            )

        except Exception as error:
            print("INFOGRAPHIC ERROR:", repr(error))

            await update.callback_query.message.reply_text(
                "❌ Infografika yaratishda xatolik yuz berdi."
            )

    else:
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
    context.user_data["image_path"] = str(path)
    image_data = base64.b64encode(path.read_bytes()).decode()

    prompt = """
Siz Uzum marketplace uchun avtomobil ehtiyot qismlari bo‘yicha professional SEO mutaxassisi va mahsulot identifikatsiyasi yordamchisisiz.

Rasmni juda ehtiyotkorlik bilan tahlil qiling.

MUHIM QOIDALAR:
1. Rasmda ko‘rinmagan ma'lumotni UYDIRMANG.
2. Mahsulot nomini uning haqiqiy shakli va konstruksiyasiga qarab aniqlang.
3. Brend faqat logotip, yorliq yoki qadoqdan aniq ko‘rinsa yozilsin.
4. OEM raqam faqat rasmda aniq o‘qilsa yozilsin.
5. OEM raqamni taxmin qilib yozmang.
6. Avtomobil mosligini faqat rasm, yorliq yoki aniq ko‘rinadigan ma'lumot asosida yozing.
7. Agar mos avtomobil modeli aniq bo‘lmasa, "Aniqlash uchun OEM/VIN kerak" deb yozing.
8. Chevrolet, GM, Ravon yoki boshqa avtomobil modelini shunchaki ehtimol bilan qo‘shmang.
9. Mahsulot boshqa detal bilan adashtirilishi mumkin bo‘lsa, eng ehtiyotkor variantni tanlang.
10. SEO kuchli bo‘lsin, lekin yolg‘on ma'lumot bo‘lmasin.

Uzum marketplace uchun quyidagi JSON formatida javob bering:

{
  "title_uz": "",
  "title_ru": "",
  "category": "",
  "brand": "",
  "oem": "",
  "compatibility": "",
  "description_uz": "",
  "description_ru": "",
  "keywords": "",
  "benefits": [
    "",
    "",
    "",
    "",
    ""
  ]
}

TALABLAR:

title_uz:
- 60-100 belgigacha.
- Mahsulotning aniq nomi.
- Agar ma'lum bo‘lsa avtomobil modeli.
- Agar ma'lum bo‘lsa brend.
- Agar ma'lum bo‘lsa OEM.

title_ru:
- Rus tilida.
- 60-100 belgigacha.
- Xuddi shu mahsulot haqida.

category:
- Avtomobil ehtiyot qismlarining aniq kategoriyasi.

brand:
- Faqat aniq ko‘ringan brend.
- Aniqlanmasa: "Aniqlanmagan".

oem:
- Faqat aniq o‘qilgan OEM.
- Aniqlanmasa: "Aniqlanmagan".

compatibility:
- Faqat ishonchli aniqlangan avtomobil modellari.
- Taxmin qilmang.

description_uz:
- Uzum uchun sotuvga yo‘naltirilgan, professional o‘zbekcha tavsif.
- Mahsulot vazifasi, materiali va qo‘llanilishi haqida yozing.
- Noma'lum texnik ma'lumotni qo‘shmang.

description_ru:
- Xuddi shu mazmunda professional ruscha tavsif.

keywords:
- 20-30 ta kuchli SEO kalit so‘z.
- Mahsulot nomi, kategoriya, brend, OEM va faqat ma'lum avtomobil modellari.
- Kalit so‘zlarni vergul bilan ajrating.

benefits:
- Aynan mahsulotga tegishli 5 ta afzallik.
- Umumiy yoki uydirma texnik xususiyat yozmang.

Javobni faqat JSON ko‘rinishida qaytaring.
JSON tashqarisida hech qanday izoh yozmang.

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
        context.user_data["product_data"] = data
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
        keyboard = [
            [InlineKeyboardButton("🎨 Infografika yaratish", callback_data="infographic")]
        ]

        await message.reply_text(
            "Mahsulot kartasi tayyor ✅\n\n"
            "Endi premium Uzum infografika yaratishingiz mumkin:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as error:
        print("ERROR:", repr(error))

        await message.edit_text(
            "❌ Xatolik yuz berdi. Render  Logs bo‘limini tekshiring."
        )
        




def run_web_server():
    port = int(os.environ.get("PORT", "10000"))
    app.run(
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


if __name__ == "__main__":
    main()
