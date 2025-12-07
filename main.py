import os
import requests
from flask import Flask, request
from openai import OpenAI

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, json=payload)


@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" not in data:
        return "ok"

    chat_id = data["message"]["chat"]["id"]
    user_text = data["message"].get("text", "")

    # GPT ответ
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": user_text}
        ]
    )

    answer = response.choices[0].message["content"]
    send_message(chat_id, answer)

    return "ok"


@app.route("/", methods=["GET"])
def index():
    return "Telegram GPT Bot is running!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
