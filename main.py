from flask import Flask, request
import telegram
from openai import OpenAI

app = Flask(__name__)

TELEGRAM_TOKEN = "ТВОЙ_ТОКЕН"
bot = telegram.Bot(token=TELEGRAM_TOKEN)

client = OpenAI(api_key="ТВОЙ_OPENAI_KEY")

@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        # Отправляем запрос в OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": text}
            ]
        )

        # ПРАВИЛЬНЫЙ СПОСОБ!!!
        answer = response.choices[0].message.content

        bot.send_message(chat_id=chat_id, text=answer)

    return "OK"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
