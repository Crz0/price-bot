"""
أدوات مشتركة بين كل السكرابرز.

كل سكرابر لازم يصدّر دالة search(query: str) -> list[dict]
كل عنصر بالنتيجة يكون شكله:
    {"title": "...", "price": 1234.0, "currency": "SAR", "url": "https://..."}

لو ما لقى شي أو صار خطأ (تغيّر تصميم الموقع، حظر، الخ) يرجّع [] بس --
وما نطيح كل السكريبت بسبب متجر واحد فاشل.
"""
import json
import re
import requests
from .. import config


_sessions_by_host: dict = {}


def fetch_html(url: str, warm_up: bool = True) -> str | None:
    """
    يجلب HTML صفحة. لو warm_up=True (الافتراضي)، يزور الصفحة الرئيسية
    لنفس الموقع أول مرة (بنفس الجلسة/الكوكيز) قبل الصفحة المطلوبة --
    هذا يحاكي سلوك متصفح حقيقي (يدخل الموقع من الصفحة الرئيسية) وبعض
    أنظمة الحماية من البوتات تتساهل أكثر مع هذا النمط.
    """
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        host = parsed.netloc

        session = _sessions_by_host.get(host)
        if session is None:
            session = requests.Session()
            session.headers.update(config.REQUEST_HEADERS)
            _sessions_by_host[host] = session

            if warm_up:
                homepage = f"{parsed.scheme}://{host}/"
                try:
                    session.get(homepage, timeout=config.REQUEST_TIMEOUT)
                except requests.RequestException:
                    pass  # لو فشلت زيارة التسخين، نكمل ونحاول الصفحة المطلوبة بأي حال

        resp = session.get(url, timeout=config.REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return None
        return resp.text
    except requests.RequestException:
        return None


_PRICE_RE = re.compile(r"[\d]+(?:[.,]\d+)?")


def parse_price(raw) -> float | None:
    """
    يحوّل نص السعر (فيه فواصل آلاف، رموز عملة، مسافات..) إلى رقم float.
    مثال: "5,699" -> 5699.0   |   "٤٬٩٩٩" (أرقام عربية) -> غير مدعوم حالياً.
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip()
    # نشيل فواصل الآلاف، نخلي بس آخر نقطة عشرية إن وجدت
    text = text.replace(",", "")
    match = _PRICE_RE.search(text)
    if not match:
        return None
    try:
        return float(match.group())
    except ValueError:
        return None


def dedupe_lowest(results: list[dict]) -> dict | None:
    """يرجع أرخص عنصر من نتائج متجر واحد (بعد فلترة اللي ما عندهم سعر)."""
    valid = [r for r in results if r.get("price")]
    if not valid:
        return None
    return min(valid, key=lambda r: r["price"])


# ---------------------------------------------------------------------------
# استخراج بيانات مهيكلة (JSON) من الصفحة -- أوثق بكثير من تحليل النص
# المرئي، لأن مواقع التجارة الحديثة (Next.js / Nuxt / Angular Universal)
# تطبع بيانات المنتجات كـ JSON داخل <script> قبل ما "تلبّسها" HTML،
# وهالبيانات نادراً ما تتغيّر شكلها حتى لو تغيّر تصميم الصفحة بصرياً.
# ---------------------------------------------------------------------------

_NAME_KEYS = {"name", "title", "productName", "displayName"}
_PRICE_KEYS = {
    "price", "salePrice", "sellingPrice", "currentPrice",
    "finalPrice", "offerPrice", "amount", "value",
}
_URL_KEYS = {"url", "productUrl", "link", "slug"}


def extract_json_ld_products(html: str) -> list[dict]:
    """يقرأ كل <script type="application/ld+json"> ويرجع منتجات Schema.org."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    results = []
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "{}")
        except (json.JSONDecodeError, TypeError):
            continue
        for product in _walk_ld_products(data):
            title = product.get("name")
            offers = product.get("offers") or {}
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            price = parse_price(offers.get("price"))
            if title and price:
                results.append({
                    "title": title,
                    "price": price,
                    "currency": offers.get("priceCurrency", "SAR"),
                    "url": product.get("url"),
                })
    return results


def _walk_ld_products(node):
    if isinstance(node, dict):
        if node.get("@type") == "Product":
            yield node
        for value in node.values():
            yield from _walk_ld_products(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_ld_products(item)


def extract_script_json_blobs(html: str) -> list:
    """
    يلقط أي <script> محتواه JSON صريح (يبدأ بـ { أو [) -- يغطي حالات
    زي __NEXT_DATA__ (Next.js)، __NUXT__ (Nuxt)، window.__INITIAL_STATE__
    وأشباهها بدون ما نعتمد على اسم متغيّر محدد.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    blobs = []
    for script in soup.find_all("script"):
        content = script.string
        if not content:
            continue
        content = content.strip()
        if not (content.startswith("{") or content.startswith("[")):
            # جرب حالة "window.X = {...};" الشائعة
            match = re.search(r"=\s*(\{.*\}|\[.*\])\s*;?\s*$", content, re.DOTALL)
            if not match:
                continue
            content = match.group(1)
        try:
            blobs.append(json.loads(content))
        except (json.JSONDecodeError, ValueError):
            continue
    return blobs


def find_price_name_pairs(node, _depth: int = 0) -> list[dict]:
    """
    يمشي بأي هيكل JSON (بغض النظر عن شكله) ويلقط أي "كائن" فيه مفتاح
    شبيه بالاسم ومفتاح شبيه بالسعر مع بعض -- هذا يخلينا ما نعتمد على
    مسار (path) ثابت بالـ JSON اللي ممكن يتغيّر مع أي تحديث بالموقع.
    """
    results = []
    if _depth > 12:  # حماية من تكرار لا نهائي بهياكل غريبة
        return results

    if isinstance(node, dict):
        name_val = None
        price_val = None
        for k, v in node.items():
            if k in _NAME_KEYS and isinstance(v, str) and v.strip():
                name_val = v.strip()
            elif k in _PRICE_KEYS:
                if isinstance(v, (int, float)):
                    price_val = float(v)
                elif isinstance(v, dict):
                    # مثال: {"price": {"value": 123, "currency": "SAR"}}
                    inner = v.get("value") or v.get("amount")
                    if isinstance(inner, (int, float)):
                        price_val = float(inner)
        if name_val and price_val and price_val > 20:
            url_val = None
            for k in _URL_KEYS:
                if isinstance(node.get(k), str):
                    url_val = node[k]
                    break
            results.append({"title": name_val, "price": price_val, "url": url_val})

        for v in node.values():
            results.extend(find_price_name_pairs(v, _depth + 1))

    elif isinstance(node, list):
        for item in node:
            results.extend(find_price_name_pairs(item, _depth + 1))

    return results
