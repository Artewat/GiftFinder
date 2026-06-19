"""Общая настройка тестов. tests/conftest.py

Дефолтные env-переменные, чтобы config/llm/db создавались без реальных секретов
(движок БД и клиент nano-gpt конструируются, но никуда не подключаются).
ВАЖНО: имена переменных подгони под свой config.py, если отличаются.
"""
import os

os.environ.setdefault("DATABASE_URL",
                      "postgresql+asyncpg://user:pass@localhost:5433/gifts")
os.environ.setdefault("NANOGPT_API_KEY", "test-key")
os.environ.setdefault("NANOGPT_BASE_URL", "http://localhost/v1")
os.environ.setdefault("NANOGPT_MODEL", "deepseek/deepseek-v3.2")
