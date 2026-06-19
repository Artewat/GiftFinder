"""Тарифы и лимит. backend/app/routers/billing.py
Подключи в main.py:  app.include_router(billing_router)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.db import async_session
from app.models import User
from app.schemas import UsageOut, UserOut
from app.usage import FREE_DAILY_LIMIT, get_today_count

router = APIRouter(prefix="/api", tags=["billing"])


@router.post("/billing/upgrade", response_model=UserOut)
async def upgrade(user: User = Depends(get_current_user)):
    # ЗАГЛУШКА ОПЛАТЫ: реальный платёжный шлюз (ЮKassa/Stripe + вебхук) —
    # точка расширения. Здесь просто переключаем тариф.
    async with async_session() as session:
        db_user = await session.get(User, user.id)
        db_user.tier = "premium"
        await session.commit()
        await session.refresh(db_user)
    return db_user


@router.post("/billing/downgrade", response_model=UserOut)
async def downgrade(user: User = Depends(get_current_user)):
    # Удобно для демо/тестов: вернуть free и снова показать лимит.
    async with async_session() as session:
        db_user = await session.get(User, user.id)
        db_user.tier = "free"
        await session.commit()
        await session.refresh(db_user)
    return db_user


@router.get("/usage", response_model=UsageOut)
async def usage(user: User = Depends(get_current_user)):
    if user.tier == "premium":
        return UsageOut(tier="premium", limit=None, used=0, remaining=None)
    async with async_session() as session:
        used = await get_today_count(session, user.id)
    return UsageOut(
        tier="free",
        limit=FREE_DAILY_LIMIT,
        used=used,
        remaining=max(0, FREE_DAILY_LIMIT - used),
    )
