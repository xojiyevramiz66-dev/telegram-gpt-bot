import os
import logging
import threading
from flask import Flask, request
import requests
from openai import OpenAI

TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# память – только предыдущее сообщение
last_message = {}


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)


def ask_gpt(chat_id, prompt):
    prev = last_message.get(chat_id, "")

    messages = [
        {"role": "system", "content": "Ты умный и дружелюбный Telegram ассистент."},
        {"role": "user", "content": f"Предыдущее сообщение: {prev}"},
        {"role": "user", "content": f"Текущее сообщение: {prompt}"}
    ]
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini-fast",   # ⚡ ускоренная модель
            messages=messages
        )
        reply = completion.choices[0].message.content

        # сохраняем текущее сообщение
        last_message[chat_id] = prompt

        return reply
    except Exception as e:
        return f"Ошибка GPT: {e}"


# ————————————————————————————
# 🔥 Функция обработчик в отдельном потоке
# ————————————————————————————
def process_message(chat_id, text):
    reply = ask_gpt(chat_id, text)
    send_message(chat_id, reply)


@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = request.json
    logging.info(update)

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        # ⚡ моментальный ответ Telegram (реально мгновенный)
        send_message(chat_id, "⌛ Подождите, думаю…")

        # обработка GPT в фоне
        threading.Thread(target=process_message, args=(chat_id, text)).start()

    # НЕ ждём GPT — мгновенно отвечаем Telegram
    return "OK", 200


@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
