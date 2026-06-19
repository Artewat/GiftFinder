"""
Реестр источников каталога. backend/app/scraper/registry.py

Подключение нового источника = один декоратор @register("ключ") над классом.
Запуск по ключу:  get_source("seed")  /  get_source("yml", feed_ref="...").
"""
from __future__ import annotations

from typing import Callable, Dict, List

# ключ источника -> фабрика, создающая FeedSource
_REGISTRY: Dict[str, Callable[..., "object"]] = {}


def register(key: str):
    """Декоратор регистрации источника под строковым ключом."""
    def deco(factory: Callable[..., "object"]):
        _REGISTRY[key] = factory
        return factory
    return deco


def get_source(key: str, **config):
    load_sources()
    if key not in _REGISTRY:
        raise KeyError(
            f"Источник '{key}' не зарегистрирован. Доступны: {available_sources()}"
        )
    return _REGISTRY[key](**config)


def available_sources() -> List[str]:
    load_sources()
    return sorted(_REGISTRY)


_loaded = False


def load_sources() -> None:
    """Импортирует модули-источники, чтобы сработали их декораторы @register.
    Новый источник? — добавь сюда строку импорта (это и есть «пара кликов»)."""
    global _loaded
    if _loaded:
        return
    from . import feed_source   # noqa: F401  -> регистрирует "yml"
    from . import seed_source   # noqa: F401  -> регистрирует "seed"
    from . import html_source   # noqa: F401  -> регистрирует "html" (заглушка)
    from . import api_source    # noqa: F401  -> регистрирует "api"  (заглушка)
    _loaded = True
