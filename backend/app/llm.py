import logging

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.nanogpt_api_key, base_url=settings.nanogpt_base_url)


async def chat_json(system: str, user: str) -> str:
    """Запрос к LLM, ожидающий JSON в ответе.

    Включаем JSON-режим (`response_format=json_object`): модель обязана вернуть
    валидный JSON-объект без обёрток/прозы — это резко снижает число случаев,
    когда ответ не парсится и курирование падает в фолбэк без обоснований.
    Не все модели/прокси принимают этот параметр, поэтому при ошибке — повтор
    без него (мягкая деградация).
    """
    base = dict(
        model=settings.nanogpt_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    try:
        response = await client.chat.completions.create(
            **base, response_format={"type": "json_object"}
        )
    except Exception as exc:  # noqa: BLE001 — модель не поддержала JSON-режим
        logger.warning("chat_json: JSON-режим недоступен (%s), повтор без него", exc)
        response = await client.chat.completions.create(**base)
    return response.choices[0].message.content or ""
