import logging
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.auth import get_current_user
from app.config import settings
from app.db import async_session, engine
from app.models import User
from app.schemas import HealthResponse, SearchRequest, SearchResponse
from app.search import search_gifts
from app.scheduler import run_all_feeds, start_scheduler, stop_scheduler
from app.usage import FREE_DAILY_LIMIT, get_today_count, increment_usage
from app.routers.auth import router as auth_router
from app.routers.billing import router as billing_router
from app.routers.wishlist import router as wishlist_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Gift Finder API", lifespan=lifespan)

# CORS с куками: конкретный origin + credentials (со звёздочкой "*" браузер запретит)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(wishlist_router)


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    db_status = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return HealthResponse(status="ok", database=db_status)


@app.post("/api/search", response_model=SearchResponse)
async def search(req: SearchRequest, user: User = Depends(get_current_user)) -> SearchResponse:
    query = req.query.strip()
    if not query:
        return SearchResponse(results=[])      # пустой запрос лимит не тратит

    # лимит проверяем только для free
    if user.tier != "premium":
        async with async_session() as session:
            used = await get_today_count(session, user.id)
        if used >= FREE_DAILY_LIMIT:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": "Дневной лимит поисков исчерпан",
                    "limit": FREE_DAILY_LIMIT,
                    "used": used,
                },
            )

    results = await search_gifts(query)

    # инкремент ПОСЛЕ успешного поиска (упавший поиск лимит не сжигает),
    # независимо от числа карточек (иначе можно фармить лимит)
    async with async_session() as session:
        await increment_usage(session, user.id)

    return SearchResponse(results=results)


@app.post("/api/admin/ingest")
async def admin_ingest(background: BackgroundTasks):
    """Ручной запуск сбора (тест, чтобы не ждать расписания)."""
    background.add_task(run_all_feeds)
    return {"status": "started"}
