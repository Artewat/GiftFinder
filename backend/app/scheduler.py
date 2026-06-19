"""
Еженедельный планировщик сбора каталога. backend/app/scheduler.py

run_all_feeds() резолвит источники через реестр и гоняет ingest.
Один и тот же код используется планировщиком и ручным триггером.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.scraper.registry import get_source
from app.scraper.ingest_feed import ingest

logger = logging.getLogger(__name__)

# TODO: позже вынеси в config.py / .env. Источники для еженедельного сбора.
# Сейчас активен seed (заглушки). Реальный источник добавляешь записью ниже.
FEEDS: list[dict] = [
    {"key": "seed", "config": {}, "deeplink": None, "prune": True},
    # {"key": "yml",
    #  "config": {"feed_ref": "https://shop.ru/yml", "source_name": "shop"},
    #  "deeplink": "https://ad.admitad.com/g/XXXXX/?ulp={url}", "prune": True},
]

_scheduler: AsyncIOScheduler | None = None


async def run_all_feeds() -> None:
    """Прогон ingest по всем источникам из FEEDS. Планировщик + ручной триггер."""
    for f in FEEDS:
        logger.info("ingest start: key=%s", f["key"])
        try:
            src = get_source(f["key"], **f.get("config", {}))
            await ingest(src, deeplink_template=f.get("deeplink"),
                         prune=f.get("prune", False))
            logger.info("ingest done: key=%s", f["key"])
        except Exception:
            logger.exception("ingest failed: key=%s", f["key"])


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    _scheduler.add_job(
        run_all_feeds,
        CronTrigger(day_of_week="mon", hour=4, minute=0),  # пн 04:00 еженедельно
        id="weekly_ingest",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    logger.info("scheduler started (weekly ingest, mon 04:00 Europe/Moscow)")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("scheduler stopped")
