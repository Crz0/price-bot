"""
سكرابر أمازون السعودية (amazon.sa).

⚠️ هذا أضعف سكرابر بالمشروع. أمازون من أشد المواقع في كشف ومنع
البوتات (قد يرجع صفحة "Robot Check" / كابتشا بدل النتائج الحقيقية،
خصوصاً من عناوين IP مشتركة زي اللي تستخدمها GitHub Actions).
تعامل مع نتائجه على إنها "إضافية" مو مصدر موثوق 100%.
راجع قسم "نقاط الضعف" في README.
"""
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from .base import fetch_html, parse_price

SEARCH_URL_TEMPLATE = "https://www.amazon.sa/-/en/s?k={query}"
STORE_NAME = "Amazon.sa"


def search(query: str) -> list[dict]:
    url = SEARCH_URL_TEMPLATE.format(query=quote_plus(query))
    html = fetch_html(url)
    if not html:
        return []

    # لو رجع صفحة كابتشا/حظر، ما راح نلقى العناصر المتوقعة -- نرجع [] بهدوء
    soup = BeautifulSoup(html, "html.parser")
    if soup.find("form", {"action": "/errors/validateCaptcha"}):
        return []

    results = []
    cards = soup.find_all("div", {"data-component-type": "s-search-result"})
    for card in cards:
        title_el = card.select_one("h2 a span") or card.select_one("h2 span")
        price_el = card.select_one("span.a-price span.a-offscreen")
        link_el = card.select_one("h2 a")

        if not price_el or not link_el:
            continue

        price = parse_price(price_el.get_text(strip=True))
        if price is None:
            continue

        href = link_el.get("href", "")
        if href.startswith("/"):
            href = "https://www.amazon.sa" + href

        results.append({
            "title": title_el.get_text(strip=True) if title_el else query,
            "price": price,
            "currency": "SAR",
            "url": href,
        })

    return results
