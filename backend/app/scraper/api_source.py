"""
Каркас коннектора к товарному API стороннего сервиса.
backend/app/scraper/api_source.py

ЗАГЛУШКА: конфигом задаёшь base_url / api_key / endpoint / маппинг полей —
и API подключён. Парсинг ответа = переопределить _request под формат сервиса.
Пока ни один сервис не подключён.

Подключение API = подкласс или конфиг + @register("ключ").
Зависимость при реальной реализации: httpx.
"""
from __future__ import annotations

from typing import Iterator, List, Optional

from .feed_source import FeedCategory, FeedOffer, FeedSource
from .registry import register

# Маппинг: поле FeedOffer -> ключ в JSON-ответе API. Под каждый сервис свой.
DEFAULT_FIELD_MAP = {
    "external_id": "id",
    "name": "title",
    "price": "price",
    "url": "link",
    "picture": "image",
    "description": "description",
    "category_external_id": "category_id",
}


@register("api")
class ApiConnectorSource(FeedSource):
    source_name = "api"

    def __init__(
        self,
        base_url: str = "",
        api_key: Optional[str] = None,
        endpoint: str = "",
        field_map: Optional[dict] = None,
        source_name: str = "api",
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.endpoint = endpoint
        self.field_map = field_map or DEFAULT_FIELD_MAP
        self.source_name = source_name

    # --- запрос к API (переопредели под формат/пагинацию сервиса) ----------
    def _request(self) -> List[dict]:
        """Вернуть список сырых товаров (dict) из API. Заглушка -> []."""
        # Реальная реализация (пример):
        #   import httpx
        #   headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        #   r = httpx.get(f"{self.base_url}{self.endpoint}", headers=headers, timeout=30)
        #   r.raise_for_status()
        #   return r.json()["items"]
        return []

    # --- сырой item -> FeedOffer по field_map (обычно трогать не нужно) ----
    def _map_item(self, item: dict) -> Optional[FeedOffer]:
        fm = self.field_map
        url = item.get(fm["url"])
        name = item.get(fm["name"])
        if not url or not name:
            return None
        raw_price = item.get(fm["price"])
        try:
            price = float(raw_price) if raw_price is not None else None
        except (TypeError, ValueError):
            price = None
        return FeedOffer(
            external_id=str(item.get(fm["external_id"]) or url),
            name=str(name),
            price=price,
            currency="RUB",
            url=str(url),
            category_external_id=(
                str(item[fm["category_external_id"]])
                if item.get(fm["category_external_id"]) is not None else None
            ),
            picture=item.get(fm["picture"]),
            description=item.get(fm["description"]),
        )

    def categories(self) -> Iterator[FeedCategory]:
        return iter(())

    def offers(self) -> Iterator[FeedOffer]:
        for raw in self._request():
            offer = self._map_item(raw)
            if offer is not None:
                yield offer


# Пример подключения конкретного API (раскомментируй и заполни):
#
# @register("some_api")
# class SomeApiSource(ApiConnectorSource):
#     def __init__(self, **kw):
#         super().__init__(
#             base_url="https://api.service.com",
#             endpoint="/v1/products",
#             field_map={**DEFAULT_FIELD_MAP, "name": "product_name"},
#             source_name="some_api", **kw,
#         )
