"""
Сменный модуль-источник каталога.

Идея: всё, что снаружи (ingest), работает с абстракцией FeedSource.
Сегодня это YmlFeedSource поверх локального/публичного YML-фида,
завтра — точно такой же класс поверх фида из Admitad. Код ingest
не меняется, меняется только реализация источника и URL фида.

Кладётся в backend/app/scraper/feed_source.py
Зависимости: только стандартная библиотека (xml.etree). Для очень
больших фидов (сотни МБ) можно заменить ElementTree на lxml.etree —
API iterparse совпадает, скорость выше.
"""
from __future__ import annotations

import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

from .registry import register


# --- нормализация значений из фида (без БД и сети, легко тестируется) --------

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def clean_text(value: Optional[str]) -> Optional[str]:
    """Снимает HTML-теги, раскрывает сущности (&amp;, &nbsp;), схлопывает
    пробелы. Пустая/пробельная строка -> None."""
    if value is None:
        return None
    text = _TAG_RE.sub("", value)
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    text = _WS_RE.sub(" ", text).strip()
    return text or None


def parse_price(value: Optional[str]) -> Optional[float]:
    """'2 490,00' -> 2490.0, '8990' -> 8990.0. Нечисловое/None -> None."""
    if value is None:
        return None
    s = str(value).replace("\xa0", "").replace(" ", "").replace(",", ".").strip()
    try:
        return float(s)
    except ValueError:
        return None


def norm_currency(value: Optional[str]) -> str:
    """Нормализует код валюты. Пусто -> 'RUB', 'RUR' -> 'RUB'."""
    if not value:
        return "RUB"
    code = value.strip().upper()
    return "RUB" if code == "RUR" else code


# --- единый формат данных, который отдаёт любой источник --------------------

@dataclass
class FeedCategory:
    external_id: str                  # id категории внутри фида
    name: str
    parent_external_id: Optional[str] # id родителя внутри фида (или None)


@dataclass
class FeedOffer:
    external_id: str                  # id товара внутри фида
    name: str
    price: Optional[float]
    currency: str
    url: str                          # ссылка на товар в магазине-источнике
    category_external_id: Optional[str]
    picture: Optional[str] = None
    description: Optional[str] = None
    vendor: Optional[str] = None
    available: bool = True


class FeedSource(ABC):
    """Базовый интерфейс источника. Любой новый источник (другой фид,
    Admitad, CSV) реализует эти два метода — остальной код не трогаем."""

    source_name: str = "unknown"

    @abstractmethod
    def categories(self) -> Iterator[FeedCategory]:
        ...

    @abstractmethod
    def offers(self) -> Iterator[FeedOffer]:
        ...


# --- конкретная реализация под YML (Yandex Market Language) -----------------

@register("yml")
class YmlFeedSource(FeedSource):
    """
    Источник поверх YML-фида.

    feed_ref — это либо URL (http/https), либо путь к локальному файлу.
    Большие фиды качаем на диск один раз и парсим локально (так стабильнее,
    чем читать гигабайты по сети на лету).
    """

    def __init__(
        self,
        feed_ref: str,
        source_name: str = "yml",
        cache_path: str | Path = "/tmp/feed.xml",
        max_offers: Optional[int] = None,
    ) -> None:
        self.feed_ref = feed_ref
        self.source_name = source_name
        self.cache_path = Path(cache_path)
        self.max_offers = max_offers
        self._local_path: Optional[Path] = None

    # скачать (если URL) или просто использовать локальный путь
    def _ensure_local(self) -> Path:
        if self._local_path is not None:
            return self._local_path
        if self.feed_ref.startswith(("http://", "https://")):
            req = urllib.request.Request(
                self.feed_ref,
                headers={"User-Agent": "Mozilla/5.0 (gift-finder feed fetcher)"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp, \
                 open(self.cache_path, "wb") as f:
                f.write(resp.read())
            self._local_path = self.cache_path
        else:
            self._local_path = Path(self.feed_ref)
        return self._local_path

    @staticmethod
    def _text(elem: ET.Element, tag: str) -> Optional[str]:
        child = elem.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return None

    def categories(self) -> Iterator[FeedCategory]:
        path = self._ensure_local()
        # iterparse не держит весь файл в памяти
        for _event, elem in ET.iterparse(path, events=("end",)):
            if elem.tag == "category":
                cid = elem.get("id")
                name = clean_text(elem.text)
                if cid and name:
                    yield FeedCategory(
                        external_id=cid,
                        name=name,
                        parent_external_id=elem.get("parentId"),
                    )
            # как только дошли до <offers> — категории кончились
            if elem.tag == "offers":
                elem.clear()
                break

    def offers(self) -> Iterator[FeedOffer]:
        path = self._ensure_local()
        emitted = 0
        for _event, elem in ET.iterparse(path, events=("end",)):
            if elem.tag != "offer":
                continue
            if self.max_offers is not None and emitted >= self.max_offers:
                elem.clear()
                break
            price = parse_price(self._text(elem, "price"))
            url = self._text(elem, "url")
            name = clean_text(self._text(elem, "name"))
            if not url or not name:
                # битый оффер — пропускаем, а не падаем
                elem.clear()
                continue
            yield FeedOffer(
                external_id=elem.get("id") or url,
                name=name,
                price=price,
                currency=norm_currency(self._text(elem, "currencyId")),
                url=url,
                category_external_id=self._text(elem, "categoryId"),
                picture=self._text(elem, "picture"),
                description=clean_text(self._text(elem, "description")),
                vendor=self._text(elem, "vendor"),
                available=elem.get("available", "true").lower() != "false",
            )
            emitted += 1
            elem.clear()  # освобождаем память после каждого оффера
