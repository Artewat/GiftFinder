"""Учёт дневного лимита поисков. backend/app/usage.py"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models import SearchUsage

FREE_DAILY_LIMIT = 5
_TZ = ZoneInfo("Europe/Moscow")   # «день» считаем в одной зоне (как планировщик)


def today():
    return datetime.now(_TZ).date()


async def get_today_count(session, user_id: int) -> int:
    res = await session.execute(
        select(SearchUsage.count).where(
            SearchUsage.user_id == user_id,
            SearchUsage.date == today(),
        )
    )
    return res.scalar_one_or_none() or 0


async def increment_usage(session, user_id: int) -> int:
    """Атомарный upsert счётчика за сегодня (insert ... on conflict do update)."""
    stmt = (
        pg_insert(SearchUsage)
        .values(user_id=user_id, date=today(), count=1)
        .on_conflict_do_update(
            index_elements=["user_id", "date"],
            set_={"count": SearchUsage.count + 1},
        )
        .returning(SearchUsage.count)
    )
    res = await session.execute(stmt)
    await session.commit()
    return res.scalar_one()
