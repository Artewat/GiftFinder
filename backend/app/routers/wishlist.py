"""Список желаемого. backend/app/routers/wishlist.py
Подключи в main.py: app.include_router(wishlist_router)

Снимок товара делает БЭКЕНД из БД (источник истины), клиент шлёт только product_id.
FK product_id -> products ON DELETE SET NULL: при еженедельном prune товар может
исчезнуть, тогда product_id станет NULL, строка-снимок останется (available=false).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.auth import get_current_user
from app.db import async_session
from app.models import Product, User, WishlistItem
from app.schemas import WishlistAdd, WishlistItemOut

router = APIRouter(prefix="/api/wishlist", tags=["wishlist"])


def _to_out(item: WishlistItem) -> dict:
    return {
        "id": item.id,
        "product_id": item.product_id,
        "available": item.product_id is not None,   # SET NULL => товар выпал из каталога
        "title": item.title,
        "price": float(item.price) if item.price is not None else None,
        "currency": item.currency,
        "image_url": item.image_url,
        "product_url": item.product_url,
        "added_at": item.added_at,
    }


@router.get("", response_model=list[WishlistItemOut])
async def list_wishlist(user: User = Depends(get_current_user)):
    async with async_session() as session:
        res = await session.execute(
            select(WishlistItem)
            .where(WishlistItem.user_id == user.id)
            .order_by(WishlistItem.added_at.desc())
        )
        items = res.scalars().all()
    return [_to_out(i) for i in items]


@router.get("/ids", response_model=list[int])
async def wishlist_product_ids(user: User = Depends(get_current_user)):
    """product_id-ы доступных позиций — чтобы фронт подсветил сердечки на карточках."""
    async with async_session() as session:
        res = await session.execute(
            select(WishlistItem.product_id).where(
                WishlistItem.user_id == user.id,
                WishlistItem.product_id.isnot(None),
            )
        )
        return [r[0] for r in res.all()]


@router.post("", response_model=WishlistItemOut)
async def add(data: WishlistAdd, user: User = Depends(get_current_user)):
    async with async_session() as session:
        product = await session.get(Product, data.product_id)
        if product is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
        # идемпотентно: повторное добавление возвращает существующую позицию
        existing = await session.execute(
            select(WishlistItem).where(
                WishlistItem.user_id == user.id,
                WishlistItem.product_id == data.product_id,
            )
        )
        item = existing.scalar_one_or_none()
        if item is None:
            item = WishlistItem(
                user_id=user.id,
                product_id=product.id,
                title=product.title,
                price=product.price,
                currency=product.currency,
                image_url=product.image_url,
                product_url=product.product_url,
            )
            session.add(item)
            await session.commit()
            await session.refresh(item)
        return _to_out(item)


@router.delete("/by-product/{product_id}")
async def remove_by_product(product_id: int, user: User = Depends(get_current_user)):
    """Снять сердечко на карточке (товар доступен -> product_id известен)."""
    async with async_session() as session:
        res = await session.execute(
            select(WishlistItem).where(
                WishlistItem.user_id == user.id,
                WishlistItem.product_id == product_id,
            )
        )
        item = res.scalar_one_or_none()
        if item is not None:
            await session.delete(item)
            await session.commit()
    return {"status": "ok"}


@router.delete("/{item_id}")
async def remove_by_id(item_id: int, user: User = Depends(get_current_user)):
    """Удалить позицию со страницы «Избранное» (работает и для недоступных)."""
    async with async_session() as session:
        item = await session.get(WishlistItem, item_id)
        if item is None or item.user_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
        await session.delete(item)
        await session.commit()
    return {"status": "ok"}
