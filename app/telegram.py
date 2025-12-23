import logging
import requests
from flask import Blueprint, request, jsonify
from .config import TELEGRAM_BOT_TOKEN, BASE_URL
from .utils import parse_message, generate_script
from .storage import save_task
from .heygen import create_video_heygen

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

tg_bp = Blueprint("telegram", __name__)

@tg_bp.route("/telegram_webhook", methods=["POST"])
def telegram_webhook():
    data = request.json
    logging.info(f"Income Telegram webhook: {data}")

    # Получить chat_id и текст сообщения
    try:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")
    except Exception:
        logging.error("Некорректный формат Telegram webhook payload!")
        return jsonify({"ok": False, "description": "Invalid Telegram payload"}), 400

    # Разбрать имя и поздравление
    name, congrat_text = parse_message(text)
    if not name or not congrat_text:
        reply_text = (
            "Напиши сообщение в формате:\n"
            "Имя: текст поздравления"
        )
        send_message_telegram(chat_id, reply_text)
        return jsonify({"ok": True}), 200

    # Сгенерировать сценарий для HeyGen
    script_text = generate_script(name, congrat_text)
    # Сформировать callback_url
    callback_url = f"{BASE_URL}/heygen_webhook"
    # Запрос в HeyGen
    result = create_video_heygen(script_text, chat_id, callback_url)
    if not result or not ("video_id" in result or "task_id" in result):
        send_message_telegram(chat_id, "Извините, возникла ошибка генерации видео. Попробуйте позже.")
        logging.error(f"Ошибка вызова HeyGen: {result}")
        return jsonify({"ok": False, "description": "HeyGen error"}), 500
    # Сохранить task_id ↔ chat_id
    task_id = result.get("video_id") or result.get("task_id")
    save_task(task_id, chat_id)
    # Ответ
    send_message_telegram(chat_id, "Спасибо! Ваше видео генерируется, ссылка придет сюда в течение пары минут 🔔")
    return jsonify({"ok": True}), 200


def send_message_telegram(chat_id: int, text: str):
    payload = {"chat_id": chat_id, "text": text}
    url = f"{TELEGRAM_API_URL}/sendMessage"
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logging.exception(f"Ошибка отправки сообщения в Telegram: {e}")


def send_video_telegram(chat_id: int, video_url: str):
    payload = {"chat_id": chat_id, "video": video_url}
    url = f"{TELEGRAM_API_URL}/sendVideo"
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logging.exception(f"Ошибка отправки видео в Telegram: {e}")




