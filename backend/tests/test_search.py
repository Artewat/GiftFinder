"""Юнит-тесты пайплайна поиска с замоканным LLM (без БД и реальной модели)."""
from types import SimpleNamespace

import pytest

import app.search as search


def test_extract_json_plain():
    assert search._extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_fenced():
    assert search._extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_with_text():
    assert search._extract_json('Вот результат:\n{"a": 1}\nготово') == {"a": 1}


def test_extract_json_garbage():
    assert search._extract_json('никакого json тут нет') is None


@pytest.mark.asyncio
async def test_understand_ok(monkeypatch):
    async def fake(system, user):
        return '{"budget_max": 3000, "categories": ["Книги"]}'
    monkeypatch.setattr(search, "chat_json", fake)
    res = await search._understand("подарок до 3000", ["Книги", "Игры"])
    assert res["budget_max"] == 3000
    assert res["categories"] == ["Книги"]


@pytest.mark.asyncio
async def test_understand_degrades_on_garbage(monkeypatch):
    async def fake(system, user):
        return 'мусор без json'
    monkeypatch.setattr(search, "chat_json", fake)
    res = await search._understand("q", ["Книги"])
    assert res["categories"] == []
    assert res["budget_max"] is None


def _fake_product(pid):
    return SimpleNamespace(
        id=pid, title=f"Товар {pid}", price=100.0, currency="RUB",
        image_url=None, product_url=f"https://x/{pid}", source="test",
        description="описание",
    )


@pytest.mark.asyncio
async def test_curate_maps_picks(monkeypatch):
    async def fake(system, user):
        return '{"picks": [{"id": 2, "reason": "хорошо"}, {"id": 1, "reason": "ок"}]}'
    monkeypatch.setattr(search, "chat_json", fake)
    cands = [_fake_product(1), _fake_product(2), _fake_product(3)]
    cards = await search._curate("q", {}, cands)
    assert [c["id"] for c in cards] == [2, 1]   # порядок от модели сохранён
    assert cards[0]["reason"] == "хорошо"


@pytest.mark.asyncio
async def test_curate_fallback_on_bad_json(monkeypatch):
    async def fake(system, user):
        return 'не json вовсе'
    monkeypatch.setattr(search, "chat_json", fake)
    cands = [_fake_product(i) for i in range(1, 11)]
    cards = await search._curate("q", {}, cands)
    assert len(cards) == 8                       # фолбэк: топ-8 по вектору
    # даже в фолбэке у карточки есть непустое обоснование (а не None) — без пустых карточек
    assert all(isinstance(c["reason"], str) and c["reason"].strip() for c in cards)


@pytest.mark.asyncio
async def test_curate_array_with_match_reason(monkeypatch):
    """Модель (deepseek) часто отдаёт голый массив и поле match_reason — парсер должен это понять."""
    async def fake(system, user):
        return '[{"id": 2, "match_reason": "по интересам"}, {"id": 1, "match_reason": "в бюджете"}]'
    monkeypatch.setattr(search, "chat_json", fake)
    cands = [_fake_product(1), _fake_product(2), _fake_product(3)]
    cards = await search._curate("q", {}, cands)
    assert [c["id"] for c in cards] == [2, 1]
    assert cards[0]["reason"] == "по интересам"


@pytest.mark.asyncio
async def test_curate_picks_without_reason_get_template(monkeypatch):
    """Товары есть, но reason модель не дала -> подставляется непустой шаблон, не None."""
    async def fake(system, user):
        return '{"recommendations": [{"id": 1, "title": "x"}, {"id": 2, "title": "y"}]}'
    monkeypatch.setattr(search, "chat_json", fake)
    cands = [_fake_product(1), _fake_product(2), _fake_product(3)]
    cards = await search._curate("q", {"interests": ["рыбалка"]}, cands)
    assert [c["id"] for c in cards] == [1, 2]
    assert all(isinstance(c["reason"], str) and c["reason"].strip() for c in cards)
