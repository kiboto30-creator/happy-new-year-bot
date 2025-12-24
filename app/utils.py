import re


def parse_message(text: str):
    """Парсит текст из Telegram-сообщения. Формат: Имя: поздравление"""
    match = re.match(r"^(.+?):\s*(.+)", text.strip())
    if match:
        name, message = match.groups()
        return name.strip(), message.strip()
    return None, None


def generate_script(name: str, message: str) -> str:
    """
    Генерирует финальный текст сценария для поздравления. Можно дообогащать.
    """
    script = (
        f"{name}, поздравляю тебя с Новым годом!\n"
        f"{message}"
    )
    return script
def parse_message(text: str):
    """
    Ожидаемый формат:
    Имя: текст поздравления
    """

    if not text:
        return None, None

    text = text.strip()

    if ":" not in text:
        return None, None

    name, congrat = text.split(":", 1)

    name = name.strip()
    congrat = congrat.strip()

    if not name or not congrat:
        return None, None

    if len(name) > 50:
        return None, None

    return name, congrat





