import os
import logging
import requests
from flask import Flask, request
from openai import OpenAI

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


# ============ SEND TEXT ============
def send_text(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})


# ============ SEND VOICE ============
def send_voice(chat_id, ogg_data):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVoice"
    files = {"voice": ("voice.ogg", ogg_data)}
    data = {"chat_id": chat_id}
    requests.post(url, data=data, files=files)


# ============ GENERATE VOICE ============
def gpt_voice_answer(text):
    try:
        result = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=text,
            format="opus"  # Telegram принимает .ogg (opus)
        )
        return result.read()
    except Exception as e:
        return None


# ============ GPT TEXT ANSWER ============
def gpt_text_answer(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Ты дружелюбный ассистент."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


# ============ GPT IMAGE ANALYSIS ============
def gpt_image_answer(image_bytes):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Опиши изображение и помоги пользователю."},
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Что на изображении?"},
                    {"type": "input_image", "image": image_bytes}
                ]
            }
        ]
    )
    return response.choices[0].message.content


@app.route("/", methods=["GET"])
def home():
    return "Bot running!"


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    logging.info(update)

    if "message" not in update:
        return "OK"

    msg = update["message"]
    chat_id = msg["chat"]["id"]

    # === TEXT MESSAGE ===
    if "text" in msg:
        text = msg["text"]

        # 1. GPT text
        answer = gpt_text_answer(text)

        # 2. GPT voice
        voice_data = gpt_voice_answer(answer)

        if voice_data:
            send_voice(chat_id, voice_data)
        else:
            send_text(chat_id, answer)

        return "OK"

    # === PHOTO MESSAGE ===
    if "photo" in msg:
        file_id = msg["photo"][-1]["file_id"]

        file_info = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
        ).json()

        file_path = file_info["result"]["file_path"]

        image_file = requests.get(
            f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        ).content

        answer = gpt_image_answer(image_file)

        # Голосовой ответ
        voice_data = gpt_voice_answer(answer)

        if voice_data:
            send_voice(chat_id, voice_data)
        else:
            send_text(chat_id, answer)

        return "OK"

    return "OK"


if __name__ == "__main__":
    render_url = os.getenv("RENDER_URL")
    if render_url:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url=https://{render_url}/{BOT_TOKEN}"
        requests.get(url)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
