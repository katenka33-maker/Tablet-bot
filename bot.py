import os
import base64
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

SYSTEM_PROMPT = """Ты проверяешь расчёты веса водолазов по фото тетради.

Алгоритм расчёта:
- Все подъёмы суммируются
- Из суммы вычитаются питки (вес тары)
- Результат умножается на 0.9 (минус 10%)
- Обведённые в кружок цифры — чистый вес одного захода
- Итог на водолаза — сумма всех заходов

Твоя задача:
1. Внимательно прочитай все цифры на фото
2. Проверь каждый расчёт по формуле: (сумма подъёмов − питки) × 0.9
3. Сравни с обведёнными цифрами
4. Сообщи ТОЛЬКО об ошибках — укажи имя водолаза, заход и правильное значение
5. Если все расчёты верны — напиши "Все расчёты верны ✅"

Отвечай кратко и чётко. Только по делу."""

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Фото получено, проверяю расчёты...")

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    
    image_bytes = bytes(await file.download_as_bytearray())
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "anthropic/claude-sonnet-4-5",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": "Проверь все расчёты на этом фото."
                            }
                        ]
                    }
                ]
            }
        )

    result = response.json()
    answer = result["choices"][0]["message"]["content"]
    await update.message.reply_text(answer)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📷 Отправь фото тетради с расчётами — я проверю все цифры.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
