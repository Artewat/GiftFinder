# Gift Finder

MVP сервиса для подбора подарков с ИИ-ассистентом.

## Запуск

1. Скопируйте `.env.example` в `.env` и заполните значения (nano-gpt ключ и т.д.).
2. Поднимите всё одной командой:

```bash
docker compose up --build
```

3. Применить миграции БД (после старта контейнеров):

```bash
docker compose exec backend alembic upgrade head
```

Сервисы:

- Backend (FastAPI): http://localhost:8000 — документация на http://localhost:8000/docs
- Frontend (React/Vite): http://localhost:5173
- Postgres (pgvector): localhost:5433

## Проверка

- `GET /api/health` — статус приложения и БД.

## Загрузка каталога из YML-фида

```bash
docker compose exec backend python -m app.scraper.ingest_feed \
  --feed app/scraper/sample_feed.xml --source demo
```

С реальным фидом и партнёрским диплинком:

```bash
docker compose exec backend python -m app.scraper.ingest_feed \
  --feed "https://shop.ru/yml" --source shopname \
  --deeplink "https://ad.admitad.com/g/XXXXX/?ulp={url}"
```

Запуск идемпотентен — повторный прогон обновляет существующие товары
(upsert по `(source, external_id)`), а не создаёт дубли.
