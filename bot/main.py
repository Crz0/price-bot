"""
نقطة التشغيل الرئيسية. GitHub Actions يشغّل هذا الملف كل فترة زمنية
محددة (شوف .github/workflows/price-check.yml).

كل تشغيل يسوي:
1. يجيب رسائل تيليجرام الجديدة (getUpdates) ويعالج الأوامر (add/list/remove)
2. لكل منتج متابَع، يفحص كل المتاجر ويلقى أرخص سعر
3. لو السعر أقل من آخر مرة (أو أول مرة نلقى سعر له) -> يرسل تنبيه
4. يحفظ كل شي بملفات JSON (الـ workflow يسوي commit لها بعدين)
"""
import sys
import traceback

from . import config
from . import storage
from . import telegram_api
from . import commands
from .scrapers import STORES


def process_telegram_updates():
    offset = storage.load_offset()
    try:
        updates = telegram_api.get_updates(offset=offset if offset else None)
    except Exception as e:
        print(f"[warn] تعذر جلب تحديثات تيليجرام: {e}")
        return

    max_update_id = offset - 1

    for update in updates:
        max_update_id = max(max_update_id, update["update_id"])
        message = update.get("message") or update.get("edited_message")
        if not message:
            continue

        chat_id = message["chat"]["id"]
        text = (message.get("text") or "").strip()
        if not text:
            continue

        # --- حماية: أول رسالة توصل وما فيه AUTHORIZED_CHAT_ID معبّى ---
        if not config.AUTHORIZED_CHAT_ID:
            telegram_api.send_message(
                chat_id,
                "مرحباً! رقم الشات (chat_id) حقك هو:\n\n"
                f"{chat_id}\n\n"
                "روح لإعدادات GitHub Secrets وضيفه باسم "
                "TELEGRAM_AUTHORIZED_CHAT_ID، وبعدها البوت راح يسوي لك "
                "بس (ما يستجيب لأي حد ثاني).",
            )
            continue

        if str(chat_id) != str(config.AUTHORIZED_CHAT_ID):
            # نتجاهل أي حد غير المستخدم المصرّح له
            continue

        handle_command(text, chat_id)

    if max_update_id >= offset:
        storage.save_offset(max_update_id + 1)


def handle_command(text: str, chat_id):
    if text.startswith("/add"):
        reply, new_product = commands.handle_add(text, chat_id)
        telegram_api.send_message(chat_id, reply)
        if new_product:
            # جرّب تجيب سعره فوراً بنفس التشغيل، بدل ما ينتظر الجولة الجاية
            check_single_product(new_product, notify_always=True)

    elif text.startswith("/list"):
        telegram_api.send_message(chat_id, commands.handle_list())

    elif text.startswith("/remove"):
        telegram_api.send_message(chat_id, commands.handle_remove(text))

    elif text.startswith("/help") or text.startswith("/start"):
        telegram_api.send_message(chat_id, commands.HELP_TEXT)

    else:
        telegram_api.send_message(
            chat_id, "أمر غير معروف. اكتب /help عشان تشوف الأوامر المتاحة."
        )


def find_best_price(product_name: str) -> dict | None:
    """يفحص كل المتاجر المسجّلة ويرجع أرخص نتيجة عبر كلها."""
    best = None
    for store_name, search_fn in STORES:
        try:
            store_results = search_fn(product_name)
        except Exception as e:
            print(f"[warn] فشل سكرابر {store_name} للمنتج \"{product_name}\": {e}")
            continue

        for item in store_results:
            if not item.get("price"):
                continue
            if best is None or item["price"] < best["lowest_price"]:
                best = {
                    "lowest_price": item["price"],
                    "store": store_name,
                    "url": item["url"],
                    "title": item.get("title", product_name),
                }
    return best


def check_single_product(product: dict, notify_always: bool = False):
    prices = storage.load_prices()
    key = str(product["id"])
    previous = prices.get(key)

    best = find_best_price(product["name"])

    if best is None:
        if notify_always:
            telegram_api.send_message(
                product["chat_id"],
                f"⚠️ ما لقيت أي سعر لـ \"{product['name']}\" بعد. "
                "بحاول مرة ثانية بالجولة الجاية.",
            )
        return

    is_new = previous is None
    is_cheaper = (not is_new) and (best["lowest_price"] < previous["lowest_price"])

    if is_new or is_cheaper or notify_always:
        old_price_line = ""
        if previous and previous["lowest_price"] != best["lowest_price"]:
            old_price_line = f"\nالسعر السابق كان: {previous['lowest_price']} ر.س"

        telegram_api.send_message(
            product["chat_id"],
            f"💸 {'سعر جديد' if is_new else 'انخفض السعر'}!\n\n"
            f"📦 {product['name']}\n"
            f"💰 {best['lowest_price']} ر.س — {best['store']}{old_price_line}\n"
            f"🔗 {best['url']}",
        )

    prices[key] = best
    storage.save_prices(prices)


def check_all_products():
    data = storage.load_products()
    for product in data["products"]:
        check_single_product(product)


def main():
    try:
        process_telegram_updates()
    except Exception:
        print("[error] فشل معالجة تحديثات تيليجرام:")
        traceback.print_exc()

    try:
        check_all_products()
    except Exception:
        print("[error] فشل فحص الأسعار:")
        traceback.print_exc()


if __name__ == "__main__":
    main()
    sys.exit(0)
