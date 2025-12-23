import logging
import requests
from flask import Blueprint, request, jsonify
from config import HEYGEN_API_KEY
from storage import get_chat_by_task, remove_task

heygen_bp = Blueprint("heygen", __name__)

HEYGEN_API_URL = "https://api.heygen.com/v1/video.create"

@heygen_bp.route("/heygen_webhook", methods=["POST"])
def heygen_webhook():
    data = request.json
    logging.info(f"HeyGen webhook received: {data}")
    task_id = data.get("video_id") or data.get("task_id")
    video_url = data.get("video_url")
    metadata = data.get("metadata", {})
    chat_id = None
    if isinstance(metadata, dict):
        chat_id = metadata.get("chat_id")
    if not video_url:
        logging.error("video_url отсутствует в payload HeyGen")
        return jsonify({"ok": False, "description": "No video_url"}), 400
    if not chat_id:
        chat_id = get_chat_by_task(task_id)
    if not chat_id:
        logging.error(f"chat_id не найден для task_id {task_id}")
        return jsonify({"ok": False, "description": "No chat_id for video"}), 400
    try:
        from .telegram import send_video_telegram
        send_video_telegram(chat_id, video_url)
        remove_task(task_id)
        return jsonify({"ok": True}), 200
    except Exception as e:
        logging.exception("Ошибка при отправке видео в Telegram")
        return jsonify({"ok": False, "description": str(e)}), 500

def create_video_heygen(script_text: str, chat_id: int, callback_url: str):
    """Создаёт видео через HeyGen API."""
    payload = {
        "script_text": script_text,
        "avatar_id": "1",  # тестовый fixed avatar (захардкодить)
        "voice_id": "ru-RU-DmitryNeural", # пример для русского
        "background": "white",
        "language": "ru-RU",
        "callback_url": callback_url,
        "metadata": {"chat_id": chat_id},
    }
    headers = {"X-Api-Key": HEYGEN_API_KEY}
    try:
        resp = requests.post(HEYGEN_API_URL, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        return result
    except requests.RequestException as e:
        logging.exception(f"Ошибка HeyGen API: {e}")
        return None





