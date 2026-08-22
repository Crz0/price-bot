"""
إعدادات البوت - كل شيء يُقرأ من متغيرات البيئة (Environment Variables)
عشان ما نحط أي مفتاح سري داخل الكود مباشرة.
"""
import os

# التوكن اللي تاخذه من BotFather في تيليجرام
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# رقم الشات (chat_id) بتاعك انت بس، عشان البوت ما يستجيب لأي حد ثاني.
# أول مرة تشغل البوت وما يكون هذا معبّى، البوت بيرد على أي رسالة توصله
# ويقول لك شنو رقم الشات حقك عشان تحطه بعدين كـ secret.
AUTHORIZED_CHAT_ID = os.environ.get("TELEGRAM_AUTHORIZED_CHAT_ID", "").strip()

# كل قد ايش (بالدقايق) تتوقع يشتغل الـ workflow -- فقط للعرض في رسائل البوت
CHECK_INTERVAL_MINUTES = int(os.environ.get("CHECK_INTERVAL_MINUTES", "30"))

# مسارات ملفات التخزين (JSON) اللي تنحفظ داخل الريبو نفسه
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
PRICES_FILE = os.path.join(DATA_DIR, "prices.json")
OFFSET_FILE = os.path.join(DATA_DIR, "offset.json")

# هيدرز نستخدمها بكل طلبات السكرابنق -- تقلل احتمال ما نتحظر بسرعة
# (بس ما تضمن شي، خصوصاً مع أمازون -- شوف قسم "نقاط الضعف" في README)
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Sec-Ch-Ua": '"Chromium";v="126", "Not.A/Brand";v="24", "Google Chrome";v="126"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Cache-Control": "max-age=0",
    "Referer": "https://www.google.com/",
}

REQUEST_TIMEOUT = 25  # ثواني
