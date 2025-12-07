import os
import logging
from flask import Flask, request
import requests
from openai import OpenAI

# Загружаем переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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
                        "Ты — свободный, честный, разговорный помощник. "
                        "Отвечай естественно, как человек. "
                        "Без фраз «как ИИ». Если запрос незаконный — откажись."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.95,
            max_tokens=800
        )

        # 🚀 НОВЫЙ ПРАВИЛЬНЫЙ СПОСОБ ПОЛУЧИТЬ ТЕКСТ
        answer = response.choices[0].message.content[0].text

        return answer

    except Exception as e:
        return f"Ошибка GPT: {e}"


@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    """Обработка входящих апдейтов"""
    update = request.get_json()

    logging.info(update)

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        reply = ask_gpt(text)
        send_message(chat_id, reply)

    return "OK", 200


if __name__ == "__main__":
    RENDER_URL = os.getenv("RENDER_URL")

    if RENDER_URL:
        webhook_url = f"https://{RENDER_URL}/{BOT_TOKEN}"
        print("Устанавливаю вебхук:", webhook_url)
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_url}")

    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
