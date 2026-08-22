"""
تخزين بسيط جداً على شكل ملفات JSON داخل مجلد data/.
الـ GitHub Actions workflow هو اللي يسوي commit + push لهذي الملفات
بعد كل تشغيل، فهي تكون "قاعدة البيانات" حقتنا -- بدون أي سيرفر أو DB خارجي.
"""
import json
import os
from . import config


def _load(path: str, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return default
        return json.loads(content)


def _save(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_products() -> dict:
    return _load(config.PRODUCTS_FILE, {"products": [], "next_id": 1})


def save_products(data: dict) -> None:
    _save(config.PRODUCTS_FILE, data)


def load_prices() -> dict:
    return _load(config.PRICES_FILE, {})


def save_prices(data: dict) -> None:
    _save(config.PRICES_FILE, data)


def load_offset() -> int:
    data = _load(config.OFFSET_FILE, {"update_offset": 0})
    return data.get("update_offset", 0)


def save_offset(offset: int) -> None:
    _save(config.OFFSET_FILE, {"update_offset": offset})
