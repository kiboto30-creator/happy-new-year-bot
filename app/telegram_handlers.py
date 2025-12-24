import logging
import requests
from flask import Blueprint, request, jsonify

from config import TELEGRAM_BOT_TOKEN, BASE_URL
from utils import parse_message, generate_script
from storage import save_task
from heygen import create_video_heygen

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

tg_bp = Blueprint("telegram", __name__)


@tg_bp.route("/telegram_webhook", methods=["POST"])
def telegram_webhook():
    data = request.json
    logging.info(f"Incoming Telegram webhook: {data}")

    # 1. Игнорируем все НЕ message апдейты (my_chat_member, edited_message и т.д.)
    if not data or "message" not in data:
        return jsonify({"ok": True}), 200

    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text")

    # 2. Только текстовые сообщения
    if not text:
        send_message_telegram(chat_id, "Пожалуйста, отправь текстовое сообщение 🙂")
        return jsonify({"ok": True}), 200

    # 3. Парсинг сообщения
    try:
        name, congrat_text = parse_message(text)
    except Exception:
        logging.exception("Ошибка парсинга сообщения")
        send_message_telegram(
            chat_id,
            "Не удалось разобрать сообщение 😕\n"
            "Формат:\nИмя: текст поздравления"
        )
        return jsonify({"ok": True}), 200

    if not name or not congrat_text:
        send_message_telegram(
            chat_id,
            "Напиши сообщение в формате:\n"
            "Имя: текст поздравления"
        )
        return jsonify({"ok": True}), 200

    # 4. Генерация сценария
    script_text = generate_script(name, congrat_text)

    # 5. HeyGen callback
    callback_url = f"{BASE_URL}/heygen_webhook"
    logging.info(f"HeyGen callback_url = {callback_url}")

    # 6. Запрос в HeyGen
    result = create_video_heygen(script_text, chat_id, callback_url)

    if not result:
        send_message_telegram(chat_id, "Ошибка генерации видео 😕 Попробуйте позже.")
        return jsonify({"ok": True}), 200

    # 7. Универсальное извлечение task_id
    task_id = (
        result.get("video_id")
        or result.get("task_id")
        or result.get("data", {}).get("video_id")
    )

    if not task_id:
        logging.error(f"HeyGen unexpected response: {result}")
        send_message_telegram(chat_id, "Не удалось запустить генерацию видео 😕")
        return jsonify({"ok": True}), 200

    # 8. Сохраняем связь task_id → chat_id
    try:
        save_task(task_id, chat_id)
    except Exception:
        logging.exception("Ошибка сохранения task_id")
        send_message_telegram(chat_id, "Внутренняя ошибка 😕")
        return jsonify({"ok": True}), 200

    # 9. Ответ пользователю
    send_message_telegram(
        chat_id,
        "Спасибо! 🎉\n"
        "Видео генерируется, я пришлю его сюда, как только будет готово 🔔"
    )

    return jsonify({"ok": True}), 200


def send_message_telegram(chat_id: int, text: str):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=10).raise_for_status()
    except Exception:
        logging.exception("Ошибка отправки сообщения в Telegram")


def send_video_telegram(chat_id: int, video_url: str):
    """
    Основной способ — отправка видео.
    Если Telegram откажется, fallback — отправка ссылки.
    """
    url = f"{TELEGRAM_API_URL}/sendVideo"
    payload = {"chat_id": chat_id, "video": video_url}

    try:
        resp = requests.post(url, json=payload, timeout=20)
        resp.raise_for_status()
        return
    except Exception:
        logging.exception("sendVideo не сработал, fallback на ссылку")

    # fallback
    send_message_telegram(
        chat_id,
        f"🎬 Видео готово!\nВот ссылка:\n{video_url}"
    )






