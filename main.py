import os
import logging
import json
import threading
from flask import Flask, request
import requests
from openai import OpenAI

TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ----- Настройки таймаутов -----
TELEGRAM_REQUEST_TIMEOUT = 5  # seconds
OPENAI_REQUEST_TIMEOUT = 20   # seconds

# ----- Соответствие надписей кнопок -> внутренний ключ режима -----
LABEL_TO_MODE = {
    "общение": "default",
    "учёба": "student",
    "учеба": "student",
    "писатель": "writer",
    "писатель́": "writer",
    "переводчик": "translator",
    "кодинг": "coder",
    "код": "coder",
    "эксперт": "expert",
    "ассистент": "assistant",
    "режимы": "modes",
    "назад": "back"
}

# ---------- ОТПРАВКА СООБЩЕНИЙ ----------
def send_message(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if keyboard:
        # Telegram принимает JSON-объект в reply_markup
        payload["reply_markup"] = keyboard

    try:
        requests.post(url, json=payload, timeout=TELEGRAM_REQUEST_TIMEOUT)
    except Exception as e:
        logging.exception("Ошибка при отправке сообщения в Telegram: %s", e)


def send_chat_action(chat_id, action="typing"):
    """Показывает пользователю, что бот печатает."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendChatAction"
    payload = {"chat_id": chat_id, "action": action}
    try:
        requests.post(url, json=payload, timeout=TELEGRAM_REQUEST_TIMEOUT)
    except Exception:
        pass


# ---------- Клавиатуры ----------
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


# ---------- РЕЖИМЫ (системные подсказки) ----------
MODES = {
    "default": "Ты дружелюбный ассистент и ведёшь обычный разговор.",
    "student": "Ты помогаешь с учёбой: объясняешь темы, решаешь задачи, даёшь простые объяснения.",
    "writer": "Ты профессиональный копирайтер: создаёшь тексты, красиво формулируешь мысли.",
    "translator": "Ты переводчик: переводишь текст, исправляешь ошибки и улучшаешь стиль.",
    "coder": "Ты эксперт по программированию: объясняешь код, исправляешь баги, даёшь примеры.",
    "expert": "Ты эксперт высокого уровня: даёшь точные, структурированные и профессиональные ответы.",
    "assistant": "Ты персональный ассистент: планируешь, структурируешь задачи и помогаешь организовать дела."
}

user_mode = {}  # режимы по chat_id


# ---------- Вспом. функции ----------
def normalize_label(text: str) -> str:
    """Извлекает слово без эмодзи/регистра для поиска в LABEL_TO_MODE."""
    if not text:
        return ""
    # убираем ведущие/замыкающие пробелы, переводим в lower
    t = text.strip().lower()
    # оставим только русские буквы и латиницу и пробелы (простая нормализация)
    cleaned = []
    for ch in t:
        if ch.isalpha() or ch.isspace():
            cleaned.append(ch)
    return "".join(cleaned).strip()


# ---------- GPT: запрос к OpenAI ----------
def ask_gpt(user_id, prompt):
    # сделаем короткий системный prompt для ускорения
    mode = user_mode.get(user_id, "default")
    system_prompt = MODES.get(mode, MODES["default"])

    # защита от слишком длинных пользовательских сообщений
    if len(prompt) > 4000:
        prompt = prompt[:4000] + "\n\n(сокращённый ввод...)"

    try:
        # покажем действие typing
        send_chat_action(user_id, action="typing")

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=700,
            temperature=0.25,
            timeout=OPENAI_REQUEST_TIMEOUT  # если библиотека поддерживает
        )

        # защищаемся на случай, если ответа нет
        if completion and getattr(completion, "choices", None):
            return completion.choices[0].message.content
        return "Извините, я не смог обработать запрос."
    except Exception as e:
        logging.exception("Ошибка при обращении к OpenAI: %s", e)
        return "Ошибка сервиса GPT — попробуйте чуть позже."


# ---------- ТЕКСТ ПРИ /start ----------
def start_text():
    return (
        "<b>Привет! 👋</b>\n"
        "Я — твой ИИ-ассистент.\n\n"
        "Я умею работать в 7 разных режимах:\n"
        "💬 Общение\n📚 Учёба\n✍️ Писатель\n🔍 Переводчик\n👨‍💻 Кодинг\n🧠 Эксперт\n📋 Ассистент\n\n"
        "Выбери режим или просто напиши сообщение!"
    )


# ---------- ОБРАБОТКА WEBHOOK ----------
@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"


def handle_message_async(chat_id, text):
    """В отдельном потоке вызов GPT и отправка ответа."""
    reply = ask_gpt(chat_id, text)
    send_message(chat_id, reply)


@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = request.json
    logging.info("Update: %s", update)

    if "message" not in update:
        return "OK", 200

    message = update["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    # команда /start
    if text == "/start":
        user_mode[chat_id] = "default"
        send_message(chat_id, start_text(), keyboard=main_menu())
        return "OK", 200

    # кнопка режимы (показываем клавиатуру)
    if text == "🎭 Режимы" or text.lower() == "режимы":
        send_message(chat_id, "Выбери нужный режим 👇", keyboard=modes_keyboard())
        return "OK", 200

    if text == "⬅️ Назад" or text.lower() == "назад":
        send_message(chat_id, "Главное меню 👇", keyboard=main_menu())
        return "OK", 200

    # проверим, является ли это выбором режима через нормализацию
    normalized = normalize_label(text)  # например "общение", "учёба"
    if normalized in LABEL_TO_MODE:
        mapped = LABEL_TO_MODE[normalized]
        if mapped == "modes":
            send_message(chat_id, "Выбери режим 👇", keyboard=modes_keyboard())
            return "OK", 200
        if mapped == "back":
            send_message(chat_id, "Главное меню 👇", keyboard=main_menu())
            return "OK", 200
        # сохраняем выбранный режим
        user_mode[chat_id] = mapped
        pretty = text  # можно показывать исходную надпись
        send_message(chat_id, f"Режим <b>{pretty}</b> включён!")
        return "OK", 200

    # если текст не распознан как режим — это обычный запрос к GPT
    # запускаем в отдельном потоке, чтобы webhook быстро ответил Telegram (200)
    thread = threading.Thread(target=handle_message_async, args=(chat_id, text), daemon=True)
    thread.start()

    # Отвечаем Telegram, что получили update
    return "OK", 200


if __name__ == "__main__":
    # Для продакшна — запускай через gunicorn:
    # gunicorn -w 4 -b 0.0.0.0:10000 webhook:app
    app.run(host="0.0.0.0", port=10000)
