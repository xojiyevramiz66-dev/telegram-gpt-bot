import os
import logging
from flask import Flask, request
import requests
import threading
import time
from openai import OpenAI

# ----------------------------------------
# CONFIG
# ----------------------------------------
TELEGRAM_TOKEN = "8202650249:AAEW3DusXW-yXjrvmtSoI6FhlAJifmo-_K8"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ВСТАВЬ СВОЙ ДОМЕН Render
RENDER_URL = "YOUR_RENDER_URL_HERE"

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

user_mode = {}  # режим для каждого пользователя


# ----------------------------------------
# ОТПРАВКА СООБЩЕНИЙ
# ----------------------------------------
def send_message(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}

    if keyboard:
        payload["reply_markup"] = keyboard

    requests.post(url, json=payload)


# ----------------------------------------
# МЕНЮ
# ----------------------------------------
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


# ----------------------------------------
# РЕЖИМЫ
# ----------------------------------------
MODES = {
    "default": "Ты дружелюбный ассистент и ведёшь простой человеческий разговор.",
    "student": "Ты помощник для учёбы: объясняешь материал простым языком.",
    "writer": "Ты профессиональный копирайтер и создаёшь тексты высокого качества.",
    "translator": "Ты переводчик: переводишь, исправляешь ошибки, улучшаешь стиль.",
    "coder": "Ты эксперт программист: пишешь код, исправляешь баги, обучаешь.",
    "expert": "Ты эксперт высокого уровня: даёшь чёткие, точные и структурированные ответы.",
    "assistant": "Ты персональный ассистент: помогаешь планировать задачи и организовывать жизнь."
}


# ----------------------------------------
# GPT ОТВЕТ
# ----------------------------------------
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


# ----------------------------------------
# /start ТЕКСТ
# ----------------------------------------
def start_text():
    return (
        "<b>Привет! 👋</b>\n"
        "Я — твой ИИ-ассистент.\n\n"
        "Я умею работать в 7 разных режимах:\n"
        "💬 Общение\n📚 Учёба\n✍️ Писатель\n🔍 Переводчик\n👨‍💻 Кодинг\n🧠 Эксперт\n📋 Ассистент\n\n"
        "Выбери режим или просто напиши сообщение!"
    )


# ----------------------------------------
# FLASK
# ----------------------------------------
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
            user_mode[chat_id] = "default"
            send_message(chat_id, start_text(), keyboard=main_menu())
            return "OK"

        # Режимы
        if text == "🎭 Режимы":
            send_message(chat_id, "Выбери режим 👇", keyboard=modes_keyboard())
            return "OK"

        if text == "⬅️ Назад":
            send_message(chat_id, "Главное меню 👇", keyboard=main_menu())
            return "OK"

        # Переключение режимов
        mode_map = {
            "💬 Общение": "default",
            "📚 Учёба": "student",
            "✍️ Писатель": "writer",
            "🔍 Переводчик": "translator",
            "👨‍💻 Кодинг": "coder",
            "🧠 Эксперт": "expert",
            "📋 Ассистент": "assistant",
        }

        if text in mode_map:
            user_mode[chat_id] = mode_map[text]
            send_message(chat_id, f"Режим <b>{text}</b> включён!")
            return "OK"

        # GPT
        reply = ask_gpt(chat_id, text)
        send_message(chat_id, reply)

    return "OK", 200


# ----------------------------------------
# KEEP-ALIVE (НЕ ДАЁТ РЕНДЕРУ УСНУТЬ)
# ----------------------------------------
def keep_alive():
    while True:
        try:
            requests.get(RENDER_URL)
        except:
            pass
        time.sleep(60)


threading.Thread(target=keep_alive, daemon=True).start()


# ----------------------------------------
# RUN
# ----------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
