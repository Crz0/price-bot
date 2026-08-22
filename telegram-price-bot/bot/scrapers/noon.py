"""
سكرابر نون (noon.com) -- السعودية.

رابط البحث بالأسفل تخمين مبني على نمط روابط نون. لو رجع صفحة فاضية،
افتح نون بالمتصفح ودوّر عن منتج، وشوف شكل رابط نتائج البحث الفعلي
وحدّث SEARCH_URL_TEMPLATE.

استراتيجية الاستخراج (بالترتيب):
1. أي JSON مدمج بالصفحة (نون Next.js عادةً، فيها __NEXT_DATA__) --
   هذا أوثق مصدر لأنه بيانات خام قبل ما "تتلبّس" HTML/CSS.
2. Schema.org / JSON-LD (لو موجود).
3. خطة أخيرة: تحليل نص الكروت مباشرة -- هشة جداً، خليتها بس لو
   الطريقتين فوق ما رجعتا شي.
"""
import re
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from .base import (
    fetch_html,
    parse_price,
    extract_script_json_blobs,
    find_price_name_pairs,
    extract_json_ld_products,
)

SEARCH_URL_TEMPLATE = "https://www.noon.com/saudi-en/search/?q={query}"
STORE_NAME = "Noon"


def search(query: str) -> list[dict]:
    url = SEARCH_URL_TEMPLATE.format(query=quote_plus(query))
    html = fetch_html(url)
    if not html:
        return []

    results = _from_embedded_json(html)
    if results:
        return _normalize_urls(results)

    results = extract_json_ld_products(html)
    if results:
        return results

    return _from_card_text_fallback(html)


def _from_embedded_json(html: str) -> list[dict]:
    blobs = extract_script_json_blobs(html)
    all_results = []
    for blob in blobs:
        all_results.extend(find_price_name_pairs(blob))
    return all_results


def _normalize_urls(results: list[dict]) -> list[dict]:
    for r in results:
        r.setdefault("currency", "SAR")
        url = r.get("url")
        if url and url.startswith("/"):
            r["url"] = "https://www.noon.com" + url
        elif not url:
            r["url"] = SEARCH_URL_TEMPLATE
    return results


def _from_card_text_fallback(html: str) -> list[dict]:
    """
    ⚠️ خطة أخيرة هشة: لو نون ما رجّعت أي JSON قابل للقراءة، نحاول نلقط
    السعر من نص الكروت مباشرة. هذا عرضة للأخطاء (أرقام تتلخبط مع
    بعض، أرقام السعة "256GB" تُفهم كسعر، الخ) -- لا تعتمد عليه وحده.
    """
    soup = BeautifulSoup(html, "html.parser")
    product_links = [a for a in soup.find_all("a", href=True) if "/p/" in a["href"]]

    results = []
    for a in product_links:
        card_text = a.get_text(separator=" | ", strip=True)
        if not card_text:
            continue
        price = _extract_price_loosely(card_text)
        if price is None:
            continue
        href = a["href"]
        if href.startswith("/"):
            href = "https://www.noon.com" + href
        title_match = re.split(r"\s\|\s\d", card_text)[0]
        results.append({
            "title": title_match.strip() or "منتج من نون",
            "price": price,
            "currency": "SAR",
            "url": href,
        })
    return results


def _extract_price_loosely(text: str) -> float | None:
    cleaned = re.sub(r"\d+(\.\d+)?%", "", text)
    # لازم يكون رقم بفواصل آلاف (زي 4,999) عشان نطمّن إنه سعر مو سعة تخزين
    tokens = re.findall(r"\d{1,3}(?:,\d{3})+", cleaned)
    for tok in tokens:
        val = parse_price(tok)
        if val and val >= 50:
            return val
    return None
