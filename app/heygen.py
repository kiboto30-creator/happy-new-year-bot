import logging
import requests
from flask import Blueprint, request, jsonify
from config import HEYGEN_API_KEY
from storage import get_chat_by_task, remove_task
from telegram_handlers import send_video_telegram

heygen_bp = Blueprint("heygen", __name__)

HEYGEN_API_URL = "https://api.heygen.com/v1/video.generate"


@heygen_bp.route("/heygen_webhook", methods=["POST"])
def heygen_webhook():
    from telegram_handlers import send_video_telegram  
    data = request.json
        logging.info(f"HeyGen webhook received: {data}")
    if not data:
        return jsonify({"ok": False}), 400

    video_url = data.get("video_url")
    task_id = data.get("video_id") or data.get("task_id")

    metadata = data.get("metadata", {})
    chat_id = metadata.get("chat_id")

    if not video_url:
        logging.error("HeyGen webhook без video_url")
        return jsonify({"ok": False}), 400

    if not chat_id:
        chat_id = get_chat_by_task(task_id)

    if not chat_id:
        logging.error(f"chat_id не найден для task_id={task_id}")
        return jsonify({"ok": False}), 400

    try:
        send_video_telegram(chat_id, video_url)
        remove_task(task_id)
        return jsonify({"ok": True}), 200
    except Exception:
        logging.exception("Ошибка отправки видео в Telegram")
        return jsonify({"ok": False}), 500


def create_video_heygen(script_text: str, chat_id: int, callback_url: str):
    headers = {
        "X-Api-Key": HEYGEN_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": "anna_public_3"
                },
                "voice": {
                    "type": "text",
                    "voice_id": "ru-RU-DmitryNeural",
                    "input_text": script_text
                },
                "background": {
                    "type": "color",
                    "value": "#ffffff"
                }
            }
        ],
        "callback_url": callback_url,
        "metadata": {
            "chat_id": chat_id
        }
    }

    try:
        resp = requests.post(
            HEYGEN_API_URL,
            headers=headers,
            json=payload,
            timeout=20
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        logging.exception("Ошибка HeyGen API")
        return None









