"""Тест HTTP-контракта /api/search (search_gifts замокан, планировщик отключён).

С этапа 9 /api/search требует входа и пишет счётчик в БД. В тесте:
- get_current_user переопределяем на фейкового premium-пользователя
  (premium минует ветку лимита — проверяем именно контракт поиска);
- increment_usage глушим в app.main (именно там связано имя — иначе пойдём в БД).
"""
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.auth import get_current_user


@pytest.fixture
def client(monkeypatch):
    # не запускать планировщик в тестах
    monkeypatch.setattr("app.main.start_scheduler", lambda: None, raising=False)
    monkeypatch.setattr("app.main.stop_scheduler", lambda: None, raising=False)

    async def fake_search(query):
        return [{
            "id": 1, "title": "Товар", "price": 100.0, "currency": "RUB",
            "image_url": None, "product_url": "https://x/1",
            "source": "test", "reason": "ок",
        }]
    # search_gifts импортирован в app.main как имя
    monkeypatch.setattr("app.main.search_gifts", fake_search, raising=False)

    # инкремент счётчика лезет в БД — глушим связанное имя в app.main
    async def fake_increment(session, user_id):
        return 1
    monkeypatch.setattr("app.main.increment_usage", fake_increment, raising=False)

    from app.main import app
    # фейковый premium-пользователь вместо чтения куки
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1, tier="premium")
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_search_endpoint_returns_cards(client):
    r = client.post("/api/search", json={"query": "подарок папе"})
    assert r.status_code == 200
    data = r.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["product_url"].startswith("https://")


def test_search_empty_query(client):
    r = client.post("/api/search", json={"query": ""})
    assert r.status_code == 200
    assert r.json()["results"] == []   # зависит от обработки пустого запроса в main


def test_search_requires_auth(monkeypatch):
    """Без переопределения зависимости /api/search должен требовать вход (401)."""
    monkeypatch.setattr("app.main.start_scheduler", lambda: None, raising=False)
    monkeypatch.setattr("app.main.stop_scheduler", lambda: None, raising=False)
    from app.main import app
    with TestClient(app) as c:
        r = c.post("/api/search", json={"query": "подарок"})
    assert r.status_code == 401
