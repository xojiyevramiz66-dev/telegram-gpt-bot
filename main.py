import os
import telebot
from flask import Flask, request
from openai import OpenAI

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)


# -------- HOME PAGE --------
@app.route("/", methods=["GET"])
def home():
    return "Bot is running!", 200


# -------- TELEGRAM WEBHOOK --------
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_data = request.get_json()

    if json_data:
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])

    return "OK", 200


# -------- MESSAGE HANDLER --------
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_text = message.text

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": user_text}
            ]
        )

        answer = response.choices[0].message.content
        bot.send_message(message.chat.id, answer)

    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")


# -------- START FLASK APP --------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
