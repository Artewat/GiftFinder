"""
Загрузка каталога из любого FeedSource в БД (категории + товары + эмбеддинги).

Кладётся в backend/app/scraper/ingest_feed.py
Версия под АСИНХРОННЫЙ app.db (async SQLAlchemy 2.0).

Запуск (из backend, при поднятой БД):
    python -m app.scraper.ingest_feed --feed app/scraper/sample_feed.xml --source demo
    python -m app.scraper.ingest_feed --feed "https://shop.ru/yml" --source shopname \
        --deeplink "https://ad.admitad.com/g/XXXXX/?ulp={url}"

ТОЧКИ ИНТЕГРАЦИИ (помечены TODO):
- TODO[1]: импорт сессии и эмбеддинга — подгони под реальный app.db / app.embeddings.
- TODO[3]: поля Product — подгони, если названы иначе.
Category.name / parent_id и наличие currency/scraped_at уже подтверждены.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
from urllib.parse import quote

from sqlalchemy import select

from .feed_source import FeedSource, YmlFeedSource
from .registry import get_source

# TODO[1]: импорты под твой код.
# async_session — это async_sessionmaker из app.db. Если у тебя вместо него
# только get_session() как зависимость FastAPI — замени блок `async with`
# ниже на работу через него.
from app.db import async_session
from app.models import Category, Product
from app.embeddings import embed_passage  # после рефактора embeddings.py


def wrap_deeplink(url: str, template: str | None) -> str:
    """Оборачивает ссылку товара в партнёрский диплинк.
    template вида 'https://ad.admitad.com/g/XXXXX/?ulp={url}'.
    Без шаблона возвращает исходную ссылку (режим демо)."""
    if not template:
        return url
    return template.replace("{url}", quote(url, safe=""))


def _product_text(name: str, description: str | None) -> str:
    """Текст для эмбеддинга товара. Префикс 'passage:' НЕ добавляем здесь —
    его ставит embed_passage(), иначе будет 'passage: passage:'."""
    return name if not description else f"{name}. {description}"


async def ingest(
    source: FeedSource,
    deeplink_template: str | None = None,
    prune: bool = False,
) -> None:
    async with async_session() as session:
        # 1) категории: external_id (из фида) -> объект Category
        feed_cats = list(source.categories())
        ext_to_cat: dict[str, Category] = {}

        for fc in feed_cats:
            res = await session.execute(
                select(Category).where(Category.name == fc.name)
            )
            cat = res.scalar_one_or_none()
            if cat is None:
                cat = Category(name=fc.name)
                session.add(cat)
                await session.flush()  # чтобы появился cat.id
            ext_to_cat[fc.external_id] = cat

        # проставляем parent_id вторым проходом
        for fc in feed_cats:
            if fc.parent_external_id and fc.parent_external_id in ext_to_cat:
                ext_to_cat[fc.external_id].parent_id = ext_to_cat[
                    fc.parent_external_id
                ].id
        await session.flush()

        # 2) товары
        added = updated = skipped = 0
        seen_ids: set[str] = set()
        for off in source.offers():
            if not off.available:
                skipped += 1
                continue

            seen_ids.add(off.external_id)

            category = ext_to_cat.get(off.category_external_id)
            buy_url = wrap_deeplink(off.url, deeplink_template)
            embedding = embed_passage(_product_text(off.name, off.description))

            # upsert по (source, external_id) — повторный прогон не дублирует
            res = await session.execute(
                select(Product).where(
                    Product.source == source.source_name,
                    Product.external_id == off.external_id,
                )
            )
            product = res.scalar_one_or_none()
            if product is None:
                product = Product(
                    source=source.source_name,
                    external_id=off.external_id,
                )
                session.add(product)
                added += 1
            else:
                updated += 1

            # TODO[3]: поля Product.
            product.title = off.name
            product.description = off.description
            product.price = off.price
            product.currency = off.currency
            product.image_url = off.picture
            product.product_url = buy_url
            product.category_id = category.id if category else None
            product.embedding = embedding
            product.scraped_at = datetime.now(timezone.utc)

        # 3) prune: удаляем товары этого источника, пропавшие из выгрузки
        pruned = 0
        if prune:
            res = await session.execute(
                select(Product).where(Product.source == source.source_name)
            )
            for product in res.scalars().all():
                if product.external_id not in seen_ids:
                    await session.delete(product)
                    pruned += 1

        await session.commit()
        print(
            f"{source.source_name}: +{added} ~{updated} "
            f"(skipped available=false {skipped}) pruned={pruned}"
        )


def main() -> None:
    ap = argparse.ArgumentParser(description="Загрузка каталога в БД")
    ap.add_argument("--source-key",
                    help="ключ источника из реестра: seed | yml | html | api")
    ap.add_argument("--feed", help="URL/путь к YML (для ключа yml)")
    ap.add_argument("--source", help="имя источника в БД (по умолчанию = ключ)")
    ap.add_argument("--deeplink", default=None, help="шаблон ссылки с {url}")
    ap.add_argument("--prune", action="store_true",
                    help="удалять записи источника, пропавшие из выгрузки")
    ap.add_argument("--limit", type=int, default=None,
                    help="ограничить число офферов (тест)")
    args = ap.parse_args()

    if args.source_key == "yml" or (not args.source_key and args.feed):
        if not args.feed:
            ap.error("для yml нужен --feed")
        src = YmlFeedSource(args.feed, source_name=args.source or "yml",
                            max_offers=args.limit)
    elif args.source_key:
        # seed / html / api и любые будущие — через реестр
        src = get_source(args.source_key, source_name=args.source or args.source_key)
    else:
        ap.error("укажи --source-key (seed|yml|html|api) или --feed")

    asyncio.run(ingest(src, deeplink_template=args.deeplink, prune=args.prune))


if __name__ == "__main__":
    main()
