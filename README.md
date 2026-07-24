# 🎁 Gift Finder

**Сервис подбора подарков с ИИ-ассистентом.** Пользователь описывает ситуацию обычными словами — _«папе 55, любит рыбалку и баню, бюджет до 5000»_ — а сервис понимает запрос по смыслу, подбирает подходящие товары из каталога и объясняет, почему именно они.

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white">
  <img alt="React" src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black">
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white">
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-16%20+%20pgvector-4169E1?logo=postgresql&logoColor=white">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white">
</p>

---

## ✨ Возможности

- 🧠 **Семантический поиск** — ИИ понимает запрос по смыслу, а не по ключевым словам.
- 💬 **Объяснимый подбор** — для каждого товара ассистент поясняет, почему он подходит.
- 💰 **Уважает бюджет** — учитывает ценовые рамки из запроса.
- 🏷️ **Скидки** — у товара есть базовая цена и процент скидки; в карточке показывается зачёркнутая старая цена, итоговая цена и бейдж `−N%`.
- 📈 **Рейтинг популярности** — чем чаще товар добавляют в избранное и жмут «Купить», тем выше он в выдаче (реранкинг `relevance + вес·popularity`).
- ⭐ **Избранное** — сохранение понравившихся вариантов со снимком цены и ссылки.
- 🔁 **Без дублей** — один и тот же товар не показывается в выдаче дважды.
- 👤 **Аккаунты и тарифы** — регистрация с подтверждением пароля, подтверждение e-mail по коду, вход (JWT в httpOnly-куке), бесплатный лимит поисков и Premium.
- 💳 **Оформление Premium** — демо-форма оплаты с валидацией карты (алгоритм Луна, срок действия, CVC).
- 🌗 **Тёмная и светлая тема** — переключатель с сохранением выбора и без «мигания» при загрузке.
- 📱 **Адаптивная вёрстка** — десктоп и мобильные с бургер-меню.

---

## 🏗️ Как это работает

Поисковый конвейер построен вокруг векторного поиска и LLM:

```
Запрос пользователя
      │
      ▼
  understand ──→ LLM разбирает запрос: повод, получатель, интересы, бюджет
      │
      ▼
  candidates ──→ Векторный поиск по каталогу (pgvector, косинусная близость)
      │           + дедупликация по нормализованному названию
      ▼
   curate   ──→ LLM отбирает лучшее и формулирует объяснение к каждой карточке
      │
      ▼
 popularity ──→ Реранкинг по популярности (клики «Купить» + добавления в избранное)
      │
      ▼
   Карточки подарков с пояснениями
```

- **Эмбеддинги** — `intfloat/multilingual-e5-base` (sentence-transformers), мультиязычные.
- **LLM** — `deepseek/deepseek-v3.2` через OpenAI-совместимый API (nano-gpt).
- **Векторное хранилище** — PostgreSQL 16 с расширением `pgvector`.
- **Популярность** — итоговый ранг = `relevance + POP_WEIGHT · popularity`, где `popularity` считается из `buy_clicks` товара и числа добавлений в избранное; сортировка стабильная, поэтому при равном скоре порядок релевантности сохраняется.

---

## 🧰 Технологии

| Слой        | Технологии                                                                 |
|-------------|----------------------------------------------------------------------------|
| **Backend** | FastAPI (async), SQLAlchemy 2.x (async), Alembic, Pydantic v2              |
| **БД**      | PostgreSQL 16 + pgvector                                                    |
| **ИИ**      | sentence-transformers (e5-base), LLM через nano-gpt (OpenAI-совместимый)    |
| **Frontend**| React 18, Vite, TypeScript, Tailwind CSS, React Router 7                    |
| **Auth**    | JWT (HS256) в httpOnly-куке, bcrypt, подтверждение e-mail по коду (SMTP)    |
| **Инфра**   | Docker Compose (db / backend / frontend)                                    |

---

## 🎨 Оформление и темы

Тема реализована на **семантических токенах**, а не на `dark:`-классах:

- CSS-переменные в `src/index.css` заданы как каналы RGB (`--surface: 255 255 255`), что позволяет Tailwind использовать прозрачность (`rgb(var(--surface) / <alpha>)`).
- Блок `:root` — светлая палитра (совпадает с изначальной, поэтому светлая тема пиксель-в-пиксель прежней), блок `.dark` переопределяет те же переменные.
- Переключатель (`components/ThemeToggle.tsx`) добавляет/снимает класс `dark` на `<html>` и хранит выбор в `localStorage`.
- Инлайн-скрипт в `index.html` выставляет тему до рендера (учитывая `localStorage` и системную `prefers-color-scheme`), поэтому нет вспышки светлого фона.

---

## 🚀 Быстрый старт

### Требования
- Docker и Docker Compose
- Ключ API [nano-gpt](https://nano-gpt.com) (или другого OpenAI-совместимого провайдера)

### 1. Настройка окружения
```bash
cp .env.example .env
```
Откройте `.env` и впишите свой `NANOGPT_API_KEY`. Для подтверждения e-mail заполните SMTP-параметры (`SMTP_*`). Остальные значения можно оставить по умолчанию.

### 2. Запуск одной командой
В проекте есть скрипт `start.sh`, который поднимает контейнеры, дожидается готовности и применяет миграции:
```bash
./start.sh            # запустить
./start.sh --build    # пересобрать образы и запустить
./start.sh --seed     # запустить и загрузить демо-каталог
./start.sh down       # остановить
./start.sh logs       # смотреть логи
```

<details>
<summary>Или вручную через Docker Compose</summary>

```bash
docker compose up --build -d
docker compose exec backend alembic upgrade head
```
</details>

### 3. Открыть в браузере

| Сервис              | Адрес                                           |
|---------------------|-------------------------------------------------|
| 🖥️ Frontend          | http://localhost:5173                           |
| ⚙️ Backend (API)     | http://localhost:8000                           |
| 📖 Документация API  | http://localhost:8000/docs                      |
| 🗄️ PostgreSQL        | localhost:5433                                  |

Проверить работоспособность: `GET /api/health` — статус приложения и БД.

---

## 📦 Каталог товаров

Загрузить демонстрационный каталог:
```bash
./start.sh seed
# или напрямую:
docker compose exec backend python -m app.scraper.ingest_feed --source-key seed --prune
```

Загрузить из YML-фида (формат Яндекс.Маркета):
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

> Загрузка идемпотентна — повторный прогон обновляет существующие товары
> (upsert по `(source, external_id)`), а не создаёт дубли. Флаг `--prune`
> удаляет из БД товары, пропавшие из источника.

---

## 🧪 Тесты

```bash
docker compose exec backend pytest
```

Покрыты, в частности, шаги поискового конвейера и реранкинг по популярности (`_apply_popularity`).

---

## 📁 Структура проекта

```
site/
├── backend/                  # FastAPI-приложение
│   ├── app/
│   │   ├── routers/          # auth (+ verify-email), billing, wishlist, track
│   │   ├── scraper/          # загрузка каталога (YML-фид, seed-источник)
│   │   ├── search.py         # поисковый конвейер (understand → candidates → curate → popularity)
│   │   ├── embeddings.py     # векторизация товаров и запросов
│   │   ├── llm.py            # клиент LLM
│   │   ├── mail.py           # отправка писем (коды подтверждения)
│   │   ├── models.py         # SQLAlchemy-модели (Product со скидкой и buy_clicks и др.)
│   │   └── auth.py           # JWT, хеширование паролей
│   ├── alembic/              # миграции БД
│   └── tests/                # pytest
├── frontend/                 # React + Vite + TypeScript
│   ├── index.html            # анти-мигание темы до рендера
│   └── src/
│       ├── pages/            # Home, Search
│       ├── components/       # NavBar, GiftCard, PaymentModal, ThemeToggle
│       ├── index.css         # семантические токены темы (:root / .dark)
│       └── *.tsx             # Login/Register/VerifyEmail/Wishlist/Pricing, контекст авторизации
├── docker-compose.yml
└── start.sh                  # скрипт запуска
```

---

## 📄 Лицензия

Проект разработан в учебных целях.
