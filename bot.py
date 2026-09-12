import os, json, base64, asyncio
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from openai import OpenAI

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

TMP = Path("tmp")
TMP.mkdir(exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("📸 Tovar rasmi yuborish", callback_data="new")]]
    await update.message.reply_text(
        "🚗 Uzum AutoCard botiga xush kelibsiz!\n\n"
        "Mahsulot rasmini yuboring. Men nom, SEO tavsif, mos avtomobillar va kalit so‘zlarni tayyorlayman.",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("📸 Mahsulot rasmini yuboring.")

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🔎 Mahsulot tahlil qilinmoqda...")
    p = await update.message.photo[-1].get_file()
    path = TMP / f"{update.effective_user.id}.jpg"
    await p.download_to_drive(path)

    data = base64.b64encode(path.read_bytes()).decode()
    prompt = """Siz Uzum marketplace uchun avtomobil ehtiyot qismlari bo‘yicha SEO mutaxassisisiz.
Rasmni tahlil qiling. Noma'lum ma'lumotni uydirmang.
Quyidagi JSON formatida javob bering:
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
        r = client.responses.create(
            model="gpt-5.6",
            input=[{
                "role":"user",
                "content":[
                    {"type":"input_text","text":prompt},
                    {"type":"input_image","image_url":f"data:image/jpeg;base64,{data}"}
                ]
            }]
        )
        text = r.output_text
        # Try to extract JSON
        start_i, end_i = text.find("{"), text.rfind("}")
        obj = json.loads(text[start_i:end_i+1])
        out = (
            f"🛒 <b>UZUM TOVAR KARTOCHKASI</b>\n\n"
            f"<b>🇺🇿 Nomi:</b> {obj.get('title_uz','')}\n"
            f"<b>🇷🇺 Название:</b> {obj.get('title_ru','')}\n"
            f"<b>📂 Kategoriya:</b> {obj.get('category','')}\n"
            f"<b>🏷 Brend:</b> {obj.get('brand','')}\n"
            f"<b>🔢 OEM:</b> {obj.get('oem','')}\n"
            f"<b>🚗 Mosligi:</b> {obj.get('compatibility','')}\n\n"
            f"<b>🇺🇿 Tavsif:</b>\n{obj.get('description_uz','')}\n\n"
            f"<b>🇷🇺 Описание:</b>\n{obj.get('description_ru','')}\n\n"
            f"<b>🔑 Kalit so‘zlar:</b>\n{obj.get('keywords','')}\n\n"
            f"<b>⭐ Afzalliklar:</b>\n" +
            "\n".join("✅ "+x for x in obj.get("benefits", []))
        )
        await msg.edit_text(out, parse_mode="HTML")
        await update.message.reply_photo(photo=path.open("rb"), caption="🎨 Keyingi bosqich: 1080×1440 infografika generatorini ulash mumkin.")
    except Exception as e:
        await msg.edit_text("❌ Xatolik yuz berdi. API kalitlari va bot sozlamalarini tekshiring.")
        print(e)

def main():
    if not BOT_TOKEN or not OPENAI_API_KEY:
        raise RuntimeError("BOT_TOKEN va OPENAI_API_KEY environment variable sifatida berilishi kerak.")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, photo))
    app.run_polling()

if __name__ == "__main__":
    main()
