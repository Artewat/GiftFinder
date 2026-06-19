"""
Пайплайн ИИ-поиска подарков.

Кладётся в backend/app/search.py (заменяет заглушку).

Поток:
  1) _understand()  — 1 LLM-вызов: разбор запроса + выбор категорий -> JSON
  2) _candidates()  — без LLM: SQL по категориям/бюджету + pgvector ранжирование
  3) _curate()      — 1 LLM-вызов: выбор 6-12 лучших + обоснование -> JSON
  4) сборка карточек для API

ТОЧКА ИНТЕГРАЦИИ (TODO[LLM]): функция chat_json(system, user) -> str.
Ожидается, что llm.py её экспортирует (async, возвращает текст ответа модели).
Референсная реализация — в промпте для Claude Code.
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Optional

from sqlalchemy import select

from app.db import async_session
from app.models import Category, Product
from app.embeddings import embed_query
from app.llm import chat_json  # TODO[LLM]: async def chat_json(system, user) -> str

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Системные промпты
# --------------------------------------------------------------------------

UNDERSTAND_SYSTEM = """Ты — ассистент по подбору подарков. Проанализируй запрос \
пользователя и верни СТРОГО валидный JSON-объект. Без markdown, без ```, без \
пояснений до или после — только JSON.

Схема ответа:
{
  "recipient": строка или null,   // кому подарок (папа, подруга, коллега...)
  "occasion": строка или null,    // повод (день рождения, Новый год...)
  "interests": [строки],          // интересы и хобби получателя
  "budget_min": число или null,   // нижняя граница бюджета в рублях
  "budget_max": число или null,   // верхняя граница бюджета в рублях
  "keywords": [строки],           // ключевые слова для поиска товаров
  "categories": [строки]          // релевантные категории СТРОГО из списка ниже
}

Правила:
- В "categories" клади только точные названия из предоставленного списка \
доступных категорий. Если ничего не подходит — пустой список [].
- Бюджет: "до 5000" -> budget_max=5000, budget_min=null. "от 1000 до 3000" -> \
оба. "около 2000" -> budget_max=2000. Не указан -> оба null.
- Не добавляй других полей. Отвечай одним JSON-объектом.

Пример.
Запрос: "подарок папе-рыбаку на день рождения до 3000 рублей"
Доступные категории: Подарки, Рыбалка и туризм, Книги, Настольные игры, Кухня и дом, Хобби и творчество
Ответ:
{"recipient":"папа","occasion":"день рождения","interests":["рыбалка"],"budget_min":null,"budget_max":3000,"keywords":["рыбалка","снасти","термокружка"],"categories":["Рыбалка и туризм","Книги"]}"""


CURATE_SYSTEM = """Ты — ассистент по подбору подарков. Из списка товаров-\
кандидатов выбери лучшие под запрос пользователя и кратко объясни выбор.

Верни СТРОГО валидный JSON-объект без markdown и без ```:
{
  "picks": [
    {"id": <id товара из списка кандидатов>, "reason": "<1 предложение по-русски: почему это хороший подарок именно здесь>"}
  ]
}

Правила:
- Выбери от 6 до 12 товаров, самые подходящие — первыми. Если подходящих \
меньше 6 — верни столько, сколько есть, но не пустой список при наличии кандидатов.
- "id" бери только из предоставленных кандидатов, не выдумывай.
- "reason" — конкретно и по делу, без воды и общих фраз.
- Отвечай одним JSON-объектом."""


# --------------------------------------------------------------------------
# Утилиты
# --------------------------------------------------------------------------

def _norm_title(title: str) -> str:
    """Нормализованный ключ названия для дедупликации.

    Приводим к нижнему регистру и выкидываем пунктуацию (запятые, тире,
    кавычки), чтобы «...стали, 500 мл» и «...стали 500 мл» считались одним
    товаром. `\\w` в Python юникодный, поэтому кириллица сохраняется.
    """
    s = re.sub(r"[^\w\s]", " ", (title or "").lower())
    return re.sub(r"\s+", " ", s).strip()


def _dedup_by_title(products: list[Product]) -> list[Product]:
    """Убирает повторы одного товара из разных источников (seed/demo и т.п.).

    Список уже отсортирован по близости к запросу, поэтому оставляем первую
    (ближайшую) копию каждого названия и сохраняем порядок ранжирования.
    """
    seen: set[str] = set()
    out: list[Product] = []
    for p in products:
        key = _norm_title(p.title)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def _extract_json(text: str) -> Optional[Any]:
    """Достаёт JSON даже если модель обернула его в ``` или добавила текст."""
    if not text:
        return None
    text = text.strip()
    # снять ```json ... ``` если есть
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # запасной вариант: вырезать первый {...} или [...]
    m = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            return None
    return None


# --------------------------------------------------------------------------
# Шаги пайплайна
# --------------------------------------------------------------------------

async def _understand(query: str, category_names: list[str]) -> dict:
    user = (
        f"Запрос: {query}\n"
        f"Доступные категории: {', '.join(category_names)}"
    )
    raw = await chat_json(UNDERSTAND_SYSTEM, user)
    data = _extract_json(raw)
    if not isinstance(data, dict):
        # деградация: ничего не поняли -> чистый векторный поиск без фильтров
        return {"budget_min": None, "budget_max": None, "categories": []}
    return data


async def _category_ids(session, names: list[str]) -> list[int]:
    """Имена категорий -> id, включая дочерние (дерево неглубокое)."""
    if not names:
        return []
    res = await session.execute(select(Category).where(Category.name.in_(names)))
    selected = res.scalars().all()
    ids = {c.id for c in selected}
    if ids:
        res_children = await session.execute(
            select(Category.id).where(Category.parent_id.in_(ids))
        )
        ids.update(r[0] for r in res_children.all())
    return list(ids)


async def _candidates(
    session,
    query: str,
    cat_ids: list[int],
    budget_min: Optional[float],
    budget_max: Optional[float],
    limit: int = 40,
) -> list[Product]:
    qvec = embed_query(query)  # синхронно (torch), для запроса это ок

    def base():
        stmt = select(Product)
        if budget_min is not None:
            stmt = stmt.where(Product.price >= budget_min)
        if budget_max is not None:
            stmt = stmt.where(Product.price <= budget_max)
        return stmt.order_by(Product.embedding.cosine_distance(qvec)).limit(limit)

    stmt = base()
    if cat_ids:
        stmt = stmt.where(Product.category_id.in_(cat_ids))
    res = await session.execute(stmt)
    candidates = list(res.scalars().all())

    # фолбэк: если категорийный фильтр дал слишком мало — ищем без категорий
    if len(candidates) < 6 and cat_ids:
        res = await session.execute(base())
        candidates = list(res.scalars().all())
    # один и тот же товар может прийти из разных источников (seed/demo) —
    # убираем повторы по названию до отправки в ИИ-курирование
    return _dedup_by_title(candidates)


async def _curate(query: str, intent: dict, candidates: list[Product]) -> list[dict]:
    items = []
    for p in candidates:
        items.append({
            "id": p.id,
            "title": p.title,
            "price": int(p.price) if p.price is not None else None,
            "desc": (p.description or "")[:160],
        })
    user = (
        f"Запрос пользователя: {query}\n"
        f"Разбор запроса: {json.dumps(intent, ensure_ascii=False)}\n"
        f"Кандидаты (JSON):\n{json.dumps(items, ensure_ascii=False)}"
    )
    raw = await chat_json(CURATE_SYSTEM, user)
    data = _extract_json(raw)
    picks = data.get("picks") if isinstance(data, dict) else None

    by_id = {p.id: p for p in candidates}
    cards: list[dict] = []
    if isinstance(picks, list):
        for pick in picks:
            pid = pick.get("id") if isinstance(pick, dict) else None
            prod = by_id.get(pid)
            if prod is not None:
                cards.append(_card(prod, pick.get("reason")))

    # фолбэк: модель не дала валидных picks -> top по вектору без обоснований
    if not cards:
        for prod in candidates[:8]:
            cards.append(_card(prod, None))
    return cards


def _card(p: Product, reason: Optional[str]) -> dict:
    return {
        "id": p.id,
        "title": p.title,
        "price": float(p.price) if p.price is not None else None,
        "currency": p.currency,
        "image_url": p.image_url,
        "product_url": p.product_url,
        "source": p.source,
        "reason": reason,
    }


# --------------------------------------------------------------------------
# Точка входа
# --------------------------------------------------------------------------

async def search_gifts(query: str) -> list[dict]:
    """Главная функция: текст запроса -> список карточек для API."""
    async with async_session() as session:
        res = await session.execute(select(Category.name))
        category_names = [r[0] for r in res.all()]

        t0 = time.perf_counter()
        intent = await _understand(query, category_names)
        t1 = time.perf_counter()

        cat_ids = await _category_ids(session, intent.get("categories") or [])
        candidates = await _candidates(
            session,
            query,
            cat_ids,
            intent.get("budget_min"),
            intent.get("budget_max"),
        )
        t2 = time.perf_counter()

        if not candidates:
            logger.info(
                "search timings: understand=%.3fs select=%.3fs curate=0.000s (no candidates)",
                t1 - t0, t2 - t1,
            )
            return []

        cards = await _curate(query, intent, candidates)
        t3 = time.perf_counter()

        logger.info(
            "search timings: understand=%.3fs select=%.3fs curate=%.3fs total=%.3fs",
            t1 - t0, t2 - t1, t3 - t2, t3 - t0,
        )
        return cards
