import os
import logging
from flask import Flask, request
import requests
from openai import OpenAI

TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# хранение только предыдущего сообщения
last_message = {}


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)


def ask_gpt(chat_id, prompt):
    # получаем предыдущее сообщение (если есть)
    prev = last_message.get(chat_id, "")

    # формируем мини-контекст
    messages = [
        {"role": "system", "content": "Ты умный и дружелюбный Telegram ассистент."},
        {"role": "user", "content": f"Предыдущее сообщение: {prev}"},
        {"role": "user", "content": f"Текущее сообщение: {prompt}"}
    ]

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        reply = completion.choices[0].message.content

        # сохраняем текущее сообщение как предыдущее
        last_message[chat_id] = prompt

        return reply
    except Exception as e:
        return f"Ошибка GPT: {e}"


@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"


@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = request.json
    logging.info(update)

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        reply = ask_gpt(chat_id, text)
        send_message(chat_id, reply)

    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
