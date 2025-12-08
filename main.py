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


# ---------- ОТПРАВКА СООБЩЕНИЙ ----------
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


# ---------- ОСНОВНОЕ МЕНЮ ----------
def main_menu():
    return {
        "keyboard": [
            [{"text": "💬 Общение"}, {"text": "📚 Учёба"}],
            [{"text": "✍️ Писатель"}, {"text": "🔍 Переводчик"}],
            [{"text": "👨‍💻 Кодинг"}, {"text": "🧠 Эксперт"}],
            [{"text": "📋 Ассистент"}],
            [{"text": "🎭 Режимы"}]
        ],
        "resize_keyboard": True
    }


# ---------- СПИСОК РЕЖИМОВ ----------
def modes_keyboard():
    return {
        "keyboard": [
            [{"text": "💬 Общение"}, {"text": "📚 Учёба"}],
            [{"text": "✍️ Писатель"}, {"text": "🔍 Переводчик"}],
            [{"text": "👨‍💻 Кодинг"}, {"text": "🧠 Эксперт"}],
            [{"text": "📋 Ассистент"}],
            [{"text": "⬅️ Назад"}]
        ],
        "resize_keyboard": True
    }


# ---------- РЕЖИМЫ ----------
MODES = {
    "default": "Ты дружелюбный ассистент и ведёшь обычный разговор.",
    "student": "Ты помогаешь с учёбой: объясняешь темы, решаешь задачи, даёшь простые объяснения.",
    "writer": "Ты профессиональный копирайтер: создаёшь тексты, красиво формулируешь мысли.",
    "translator": "Ты переводчик: переводишь текст, исправляешь ошибки, делаешь стиль грамотным.",
    "coder": "Ты эксперт по программированию: объясняешь код, исправляешь баги, обучаешь языкам.",
    "expert": "Ты эксперт высокого уровня: даёшь точные, структурированные и профессиональные ответы.",
    "assistant": "Ты персональный ассистент: планируешь, структурируешь задачи, помогаешь организовать дела."
}

user_mode = {}  # режимы по chat_id


# ---------- GPT ОТВЕТ ----------
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


# ---------- ТЕКСТ ПРИ /start ----------
def start_text():
    return (
        "<b>Привет! 👋</b>\n"
        "Я — твой ИИ-ассистент.\n\n"
        "Я умею работать в 7 разных режимах:\n"
        "💬 Общение\n📚 Учёба\n✍️ Писатель\n🔍 Переводчик\n👨‍💻 Кодинг\n🧠 Эксперт\n📋 Ассистент\n\n"
        "Выбери режим или просто напиши сообщение!"
    )


# ---------- WEBHOOK ----------
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

        # старт
        if text == "/start":
            user_mode[chat_id] = "default"
            send_message(chat_id, start_text(), keyboard=main_menu())
            return "OK"

        # кнопка: режимы
        if text == "🎭 Режимы":
            send_message(chat_id, "Выбери нужный режим 👇", keyboard=modes_keyboard())
            return "OK"

        # назад
        if text == "⬅️ Назад":
            send_message(chat_id, "Главное меню 👇", keyboard=main_menu())
            return "OK"

        # установка режима
        if text == "💬 Общение":
            user_mode[chat_id] = "default"
            send_message(chat_id, "Режим <b>Общение</b> включён! 💬")
            return "OK"

        if text == "📚 Учёба":
            user_mode[chat_id] = "student"
            send_message(chat_id, "Режим <b>Учёба</b> включён! 📚")
            return "OK"

        if text == "✍️ Писатель":
            user_mode[chat_id] = "writer"
            send_message(chat_id, "Режим <b>Писатель</b> включён! ✍️")
            return "OK"

        if text == "🔍 Переводчик":
            user_mode[chat_id] = "translator"
            send_message(chat_id, "Режим <b>Переводчик</b> включён! 🔍")
            return "OK"

        if text == "👨‍💻 Кодинг":
            user_mode[chat_id] = "coder"
            send_message(chat_id, "Режим <b>Кодинг</b> включён! 👨‍💻")
            return "OK"

        if text == "🧠 Эксперт":
            user_mode[chat_id] = "expert"
            send_message(chat_id, "Режим <b>Эксперт</b> включён! 🧠")
            return "OK"

        if text == "📋 Ассистент":
            user_mode[chat_id] = "assistant"
            send_message(chat_id, "Режим <b>Ассистент</b> включён! 📋")
            return "OK"

        # GPT ОТВЕТ
        reply = ask_gpt(chat_id, text)
        send_message(chat_id, reply)

    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
