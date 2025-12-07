import os
import telebot
from flask import Flask, request
from openai import OpenAI

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RENDER_URL = os.getenv("RENDER_URL")

bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_data = request.get_json()
    if json_data:
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
    return "OK", 200


@bot.message_handler(content_types=["text"])
def handle_message(message):
    try:
        # Новый синтаксис OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": message.text}
            ]
        )

        answer = response.choices[0].message.content
        bot.send_message(message.chat.id, answer)

    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{RENDER_URL}/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
