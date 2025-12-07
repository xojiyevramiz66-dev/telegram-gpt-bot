import os
import logging
from flask import Flask, request
import requests
from openai import OpenAI

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})


def ask_gpt(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — дружелюбный помощник. Общайся естественно и живо."
                    )
                },
                {"role": "user", "content": prompt}
            ]
        )

        # ⭐ Правильный, рабочий способ получить текст
        answer = response.choices[0].message.content

        return answer

    except Exception as e:
        return f"Ошибка GPT: {e}"


@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    logging.info(update)

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        reply = ask_gpt(text)
        send_message(chat_id, reply)

    return "OK", 200


if __name__ == "__main__":
    render_url = os.getenv("RENDER_URL")
    if render_url:
        webhook_url = f"https://{render_url}/{BOT_TOKEN}"
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_url}")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
