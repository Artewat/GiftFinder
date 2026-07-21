"""Трекинг событий для рейтинга популярности. backend/app/routers/track.py
Подключи в main.py: app.include_router(track_router)

Клик «Купить» инкрементит products.buy_clicks. Без авторизации и максимально
незаметно: трекинг не должен ломать переход пользователя в магазин, поэтому на
несуществующий товар отвечаем тихо (204), а не ошибкой.
"""
from __future__ import annotations

from fastapi import APIRouter, Response, status
from sqlalchemy import update

from app.db import async_session
from app.models import Product

router = APIRouter(prefix="/api/track", tags=["track"])


@router.post("/buy/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def track_buy_click(product_id: int) -> Response:
    """Пользователь нажал «Купить» — +1 к счётчику популярности товара."""
    async with async_session() as session:
        await session.execute(
            update(Product)
            .where(Product.id == product_id)
            .values(buy_clicks=Product.buy_clicks + 1)
        )
        await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
