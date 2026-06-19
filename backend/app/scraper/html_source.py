"""
Каркас скрапера HTML-страниц. backend/app/scraper/html_source.py

ЗАГЛУШКА: базовый класс с готовым вежливым _fetch (User-Agent + rate-limit)
и обходом «категория -> листинг -> товар». Парсинг конкретного сайта живёт
в подклассе (переопредели 3 хука). Пока ни один сайт не подключён.

Подключение сайта = подкласс + @register("ключ") + реализация 3 методов.
Зависимости при реальной реализации: httpx, selectolax (или lxml).
"""
from __future__ import annotations

import time
from typing import Iterator, List, Optional

from .feed_source import FeedCategory, FeedOffer, FeedSource
from .registry import register


@register("html")
class HtmlScraperSource(FeedSource):
    source_name = "html"

    def __init__(
        self,
        base_url: str = "",
        rate_limit_s: float = 1.0,
        user_agent: str = "Mozilla/5.0 (gift-finder)",
        source_name: str = "html",
    ) -> None:
        self.base_url = base_url
        self.rate_limit_s = rate_limit_s
        self.user_agent = user_agent
        self.source_name = source_name

    # --- готовый помощник: вежливый GET (UA + пауза между запросами) -------
    def _fetch(self, url: str) -> str:
        import httpx  # ленивый импорт: заглушка импортируется без зависимости
        time.sleep(self.rate_limit_s)  # rate-limit: не долбим сайт
        resp = httpx.get(url, headers={"User-Agent": self.user_agent}, timeout=30)
        resp.raise_for_status()
        return resp.text

    # --- ХУКИ под конкретный сайт (переопредели в подклассе) ---------------
    def category_urls(self) -> List[str]:
        """Список URL страниц категорий. Заглушка -> []."""
        return []

    def parse_listing(self, html_text: str) -> List[str]:
        """Из HTML листинга достать ссылки на карточки товаров. Заглушка -> []."""
        return []

    def parse_product(self, html_text: str, url: str) -> Optional[FeedOffer]:
        """Из HTML карточки собрать FeedOffer. Заглушка -> None."""
        return None

    # --- общий обход (трогать не нужно) ------------------------------------
    def categories(self) -> Iterator[FeedCategory]:
        # для скрапера категории обычно неявные; при желании заполни в подклассе
        return iter(())

    def offers(self) -> Iterator[FeedOffer]:
        for cat_url in self.category_urls():
            try:
                listing = self._fetch(cat_url)
            except Exception:
                continue
            for product_url in self.parse_listing(listing):
                try:
                    offer = self.parse_product(self._fetch(product_url), product_url)
                except Exception:
                    continue
                if offer is not None:
                    yield offer


# Пример подключения реального сайта (раскомментируй и реализуй хуки):
#
# @register("example_shop")
# class ExampleShopSource(HtmlScraperSource):
#     def __init__(self, **kw):
#         super().__init__(base_url="https://example-shop.ru", source_name="example_shop", **kw)
#     def category_urls(self):
#         return ["https://example-shop.ru/catalog/gifts"]
#     def parse_listing(self, html_text):
#         from selectolax.parser import HTMLParser
#         tree = HTMLParser(html_text)
#         return [a.attributes.get("href") for a in tree.css("a.product-link")]
#     def parse_product(self, html_text, url):
#         from selectolax.parser import HTMLParser
#         t = HTMLParser(html_text)
#         return FeedOffer(
#             external_id=url, name=t.css_first("h1").text(strip=True),
#             price=None, currency="RUB", url=url, category_external_id=None,
#         )
