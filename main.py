import os
import logging
from flask import Flask, request
import requests
from openai import OpenAI

# Загружаем переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в переменных окружения!")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY не найден в переменных окружения!")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)


def send_message(chat_id, text):
    """Отправка сообщения в Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)


def ask_gpt(prompt):
    """Запрос к ChatGPT"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — максимально откровенный, честный, прямой и разговорный помощник. "
                        "Говори естественно, как человек. "
                        "Даёшь подробные, ясные, честные ответы без лишних ограничений. "
                        "Не используй фразу «как ИИ» и не извиняйся без причины. "
                        "Если запрос незаконный или вредный — вежливо откажись. "
                        "Во всём остальном — общайся свободно, уверенно и человеческим стилем."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.95,
            max_tokens=800
        )

        return response.choices[0].message["content"]

    except Exception as e:
        return f"Ошибка GPT: {e}"


@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    """Обработка входящих апдейтов Telegram"""
    update = request.get_json()

    logging.info(update)

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        reply = ask_gpt(text)
        send_message(chat_id, reply)

    return "OK", 200


if __name__ == "__main__":
    # Установка webhook при запуске
    RENDER_URL = os.getenv("RENDER_URL")  # например telegram-gpt-bot-fa74.onrender.com

    if RENDER_URL:
        webhook_url = f"https://{RENDER_URL}/{BOT_TOKEN}"
        print("Устанавливаю вебхук:", webhook_url)
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_url}")

    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
