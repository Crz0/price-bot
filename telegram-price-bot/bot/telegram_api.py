"""
غلاف بسيط فوق Telegram Bot API -- بدون أي مكتبة خارجية ثقيلة،
بس مكتبة requests. يكفينا: getUpdates و sendMessage.
"""
import requests
from . import config

API_BASE = "https://api.telegram.org/bot{token}/{method}"


def _call(method: str, params: dict = None) -> dict:
    if not config.BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN غير معبّى في متغيرات البيئة")
    url = API_BASE.format(token=config.BOT_TOKEN, method=method)
    resp = requests.post(url, json=params or {}, timeout=config.REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data}")
    return data["result"]


def get_updates(offset: int = None, timeout: int = 0) -> list:
    """
    يجيب الرسائل الجديدة اللي ما زلنا ما عالجناها.
    offset = آخر update_id شفناه + 1
    """
    params = {"timeout": timeout}
    if offset is not None:
        params["offset"] = offset
    return _call("getUpdates", params)


def send_message(chat_id, text: str, disable_web_page_preview: bool = True):
    return _call(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
        },
    )
