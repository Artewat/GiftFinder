from openai import AsyncOpenAI

from app.config import settings

client = AsyncOpenAI(api_key=settings.nanogpt_api_key, base_url=settings.nanogpt_base_url)


async def chat_json(system: str, user: str) -> str:
    response = await client.chat.completions.create(
        model=settings.nanogpt_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""
