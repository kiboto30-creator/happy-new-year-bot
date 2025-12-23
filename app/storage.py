# Можно заменить на SQLite при необходимости
import threading

_lock = threading.Lock()
_task_to_chat = {}
_chat_to_task = {}

def save_task(task_id: str, chat_id: int):
    with _lock:
        _task_to_chat[task_id] = chat_id
        _chat_to_task[chat_id] = task_id

def get_chat_by_task(task_id: str):
    with _lock:
        return _task_to_chat.get(task_id)

def remove_task(task_id: str):
    with _lock:
        chat_id = _task_to_chat.pop(task_id, None)
        if chat_id:
            _chat_to_task.pop(chat_id, None)




