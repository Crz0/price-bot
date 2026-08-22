"""
سكرابر إكسترا (extra.com) -- السعودية.

رابط البحث بالأسفل تخمين مبني على نمط مواقع من نفس نوع منصة إكسترا
(SAP Commerce / hybris). لو رجع صفحة فاضية أو خطأ، افتح extra.com،
دوّر عن منتج، وشوف شكل رابط نتائج البحث الفعلي وحدّث SEARCH_URL_TEMPLATE.

نعتمد أولاً على بيانات Schema.org / JSON-LD المدمجة بالصفحة (أغلب
مواقع التجارة الإلكترونية تحطها لأغراض SEO) لأنها أكثر ثباتاً من
أسماء أصناف الـ CSS اللي تتغير مع كل تحديث تصميم.
"""
import re
from urllib.parse import quote_plus

from .base import (
    fetch_html,
    parse_price,
    extract_json_ld_products,
    extract_script_json_blobs,
    find_price_name_pairs,
)

SEARCH_URL_TEMPLATE = "https://www.extra.com/en-sa/search/?q={query}"
STORE_NAME = "Extra"


def search(query: str) -> list[dict]:
    url = SEARCH_URL_TEMPLATE.format(query=quote_plus(query))
    html = fetch_html(url)
    if not html:
        return []

    results = extract_json_ld_products(html)
    if results:
        for r in results:
            r["url"] = r.get("url") or url
        return results

    blobs = extract_script_json_blobs(html)
    for blob in blobs:
        found = find_price_name_pairs(blob)
        if found:
            for r in found:
                r.setdefault("currency", "SAR")
                r["url"] = r.get("url") or url
            return found

    return _from_generic_price_pattern(html, url)


def _from_generic_price_pattern(html: str, page_url: str) -> list[dict]:
    """
    خطة بديلة أضعف: نبحث عن أرقام ملاصقة لكلمة SAR أو ر.س في النص
    ونرجع أرخصها كنتيجة وحيدة بدون عنوان دقيق.
    """
    matches = re.findall(r"(?:SAR|ر\.س)\s?([\d,]+(?:\.\d+)?)", html)
    if not matches:
        matches = re.findall(r"([\d,]+(?:\.\d+)?)\s?(?:SAR|ر\.س)", html)
    prices = [parse_price(m) for m in matches]
    prices = [p for p in prices if p and p > 20]
    if not prices:
        return []
    return [{
        "title": "(extra.com - عنوان غير مؤكد)",
        "price": min(prices),
        "currency": "SAR",
        "url": page_url,
    }]
