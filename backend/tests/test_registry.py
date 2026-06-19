"""Юнит-тесты реестра источников (без БД и сети)."""
import pytest

from app.scraper.registry import available_sources, get_source


def test_available_sources():
    assert set(available_sources()) >= {"seed", "yml", "html", "api"}


def test_seed_source():
    seed = get_source("seed")
    assert len(list(seed.categories())) == 7
    offers = list(seed.offers())
    assert len(offers) == 16
    assert all(o.currency == "RUB" for o in offers)


def test_stub_sources_empty():
    assert list(get_source("html").offers()) == []
    assert list(get_source("api").offers()) == []


def test_unknown_source_raises():
    with pytest.raises(KeyError):
        get_source("nonexistent")
