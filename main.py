import os
import logging
from flask import Flask, request
import requests

app = Flask(__name__)

BOT_TOKEN = "8202650249:AAEW3DusXW-yXjrvmtSoI6FhlAJifmo-_K8"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()

    if not data:
        return "no data"

    logging.info(f"Incoming update: {data}")

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        # Ответ бота
        reply = f"Ты написал: {text}"

        # Отправляем ответ
        requests.post(TELEGRAM_URL, json={
            "chat_id": chat_id,
            "text": reply
        })

    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
