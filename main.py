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


# ---------- Отправка сообщений ----------
def send_message(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if keyboard:
        payload["reply_markup"] = keyboard

    requests.post(url, json=payload)


# ---------- Клавиатура ----------
def main_menu():
    return {
        "keyboard": [
            [{"text": "💬 Общение"}, {"text": "📚 Учёба"}],
            [{"text": "✍️ Написать текст"}, {"text": "🔍 Проверка/Перевод"}],
            [{"text": "🎭 Режимы"}]
        ],
        "resize_keyboard": True
    }


# ---------- Режимы ----------
MODES = {
    "default": "Ты умный и дружелюбный Telegram ассистент.",
    "student": "Ты помогаешь студентам: решаешь задачи, объясняешь темы.",
    "writer": "Ты профессиональный копирайтер: красиво пишешь тексты.",
    "translator": "Ты переводчик и корректируешь ошибки.",
}

user_mode = {}  # режим для каждого пользователя


# ---------- GPT ----------
def ask_gpt(user_id, prompt):
    mode = user_mode.get(user_id, "default")

    system_prompt = MODES[mode]

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content

    except Exception as e:
        return f"Ошибка GPT: {e}"


# ---------- Приветственное сообщение ----------
def start_text():
    return (
        "<b>Привет! 👋</b>\n"
        "Я — твой ИИ-ассистент.\n\n"
        "Вот что я умею:\n"
        "• Общаться и отвечать на вопросы\n"
        "• Помогать с учёбой 📚\n"
        "• Писать тексты ✍️\n"
        "• Исправлять ошибки и переводить 🔍\n\n"
        "Выбери нужный пункт меню👇"
    )


# ---------- Webhook ----------
@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"


@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = request.json
    logging.info(update)

    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        # /start
        if text == "/start":
            send_message(chat_id, start_text(), keyboard=main_menu())
            user_mode[chat_id] = "default"
            return "OK"

        # Выбор режимов
        if text == "📚 Учёба":
            user_mode[chat_id] = "student"
            send_message(chat_id, "Режим: <b>Учёба</b> включён! 📚")
            return "OK"

        if text == "✍️ Написать текст":
            user_mode[chat_id] = "writer"
            send_message(chat_id, "Режим: <b>Писатель</b> включён! ✍️")
            return "OK"

        if text == "🔍 Проверка/Перевод":
            user_mode[chat_id] = "translator"
            send_message(chat_id, "Режим: <b>Переводчик</b> включён! 🔍")
            return "OK"

        if text == "💬 Общение":
            user_mode[chat_id] = "default"
            send_message(chat_id, "Режим: <b>Обычное общение</b> 💬")
            return "OK"

        # GPT ответ
        reply = ask_gpt(chat_id, text)
        send_message(chat_id, reply)

    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
