"""
معالجة أوامر تيليجرام: /add /list /remove /help
"""
from . import storage

HELP_TEXT = (
    "🤖 بوت متابعة أسعار المنتجات\n\n"
    "الأوامر المتاحة:\n"
    "/add <اسم المنتج> — أضف منتج جديد للمتابعة\n"
    "/list — اعرض المنتجات اللي أتابعها حالياً\n"
    "/remove <رقم> — احذف منتج (استخدم الرقم اللي يظهر بـ /list)\n"
    "/help — هذي الرسالة\n\n"
    "ملاحظة: البوت يتحقق من الأسعار كل فترة (مو فوري لحظة إرسال "
    "الأمر) لأنه يشتغل عبر GitHub Actions مجدول، مو سيرفر شغال "
    "طول الوقت."
)


def handle_add(text: str, chat_id) -> tuple[str, dict | None]:
    name = text[len("/add"):].strip()
    if not name:
        return "اكتب اسم المنتج بعد الأمر، مثال:\n/add ايفون 16 برو 256 جيجا", None

    data = storage.load_products()
    # امنع تكرار نفس الاسم
    for p in data["products"]:
        if p["name"].strip().lower() == name.lower():
            return f"المنتج \"{name}\" متابَع أصلاً (رقم {p['id']}).", None

    new_id = data.get("next_id", 1)
    product = {"id": new_id, "name": name, "chat_id": chat_id}
    data["products"].append(product)
    data["next_id"] = new_id + 1
    storage.save_products(data)

    return f"✅ تمت إضافة \"{name}\" (رقم {new_id}) للمتابعة. بجيب لك أرخص سعر أول ما ألقاه.", product


def handle_list() -> str:
    data = storage.load_products()
    products = data["products"]
    if not products:
        return "ما فيه منتجات متابَعة حالياً. أضف واحد بـ /add <اسم المنتج>"

    prices = storage.load_prices()
    lines = ["📋 المنتجات المتابَعة:\n"]
    for p in products:
        price_info = prices.get(str(p["id"]))
        if price_info:
            lines.append(
                f"#{p['id']} — {p['name']}\n"
                f"   💰 أرخص سعر معروف: {price_info['lowest_price']} ر.س "
                f"({price_info['store']})\n"
                f"   🔗 {price_info['url']}"
            )
        else:
            lines.append(f"#{p['id']} — {p['name']}\n   ⏳ ما لقينا سعر له بعد")
    return "\n\n".join(lines)


def handle_remove(text: str) -> str:
    arg = text[len("/remove"):].strip()
    if not arg.isdigit():
        return "اكتب رقم المنتج بعد الأمر، مثال:\n/remove 3\n(الأرقام تشوفها بـ /list)"

    target_id = int(arg)
    data = storage.load_products()
    before = len(data["products"])
    data["products"] = [p for p in data["products"] if p["id"] != target_id]
    if len(data["products"]) == before:
        return f"ما لقيت منتج برقم {target_id}."

    storage.save_products(data)
    prices = storage.load_prices()
    prices.pop(str(target_id), None)
    storage.save_prices(prices)
    return f"🗑️ تم حذف المنتج رقم {target_id} من المتابعة."
