#!/usr/bin/env bash
#
# Быстрый запуск Gift Finder.
#
#   ./start.sh            поднять стек + применить миграции (по умолчанию)
#   ./start.sh --build    то же, но пересобрать образы (после смены зависимостей)
#   ./start.sh --seed     то же + загрузить seed-каталог (16 товаров)
#   ./start.sh down       остановить стек (данные в томах сохраняются)
#   ./start.sh restart    перезапустить контейнеры
#   ./start.sh logs       хвост логов всех сервисов
#   ./start.sh seed       только загрузить seed-каталог в работающий стек
#   ./start.sh ps         статус контейнеров
#
set -euo pipefail

# каталог скрипта = корень compose-проекта, откуда бы его ни запускали
cd "$(dirname "$(readlink -f "$0")")"

API_URL="http://localhost:8000"
WEB_URL="http://localhost:5173"

# docker compose (v2) или docker-compose (v1)
if docker compose version >/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
else
  echo "✗ docker compose не найден. Установите Docker." >&2
  exit 1
fi

c_green() { printf '\033[32m%s\033[0m\n' "$1"; }
c_yellow() { printf '\033[33m%s\033[0m\n' "$1"; }
c_red() { printf '\033[31m%s\033[0m\n' "$1"; }

require_env() {
  if [[ ! -f .env ]]; then
    c_red "✗ Нет файла .env."
    c_yellow "  Скопируйте: cp .env.example .env  и заполните (nano-gpt ключ, SECRET_KEY и т.д.)."
    exit 1
  fi
}

wait_for_backend() {
  printf 'Жду backend (%s/api/health) ' "$API_URL"
  for _ in $(seq 1 60); do
    if curl -fs "$API_URL/api/health" >/dev/null 2>&1; then
      printf '\n'; c_green "✓ backend отвечает"; return 0
    fi
    printf '.'; sleep 2
  done
  printf '\n'; c_red "✗ backend не поднялся за ~120с. Логи: ./start.sh logs"; exit 1
}

migrate() {
  echo "→ Применяю миграции (alembic upgrade head)…"
  $DC exec -T backend alembic upgrade head
  c_green "✓ миграции применены"
}

seed() {
  echo "→ Загружаю seed-каталог…"
  $DC exec -T backend python -m app.scraper.ingest_feed --source-key seed --prune
  c_green "✓ seed-каталог загружен"
}

up() {
  local build="$1" do_seed="$2"
  require_env
  if [[ "$build" == "1" ]]; then
    echo "→ Пересборка образов…"
    $DC build
  fi
  echo "→ Поднимаю стек…"
  $DC up -d
  wait_for_backend
  migrate
  [[ "$do_seed" == "1" ]] && seed
  echo
  c_green "Готово. Сайт поднят:"
  echo "  Сайт   $WEB_URL"
  echo "  API    $API_URL/docs"
  echo "  БД     localhost:5433"
  c_yellow "Первый поиск ~30–60с (ленивая загрузка ИИ-модели)."
}

cmd="${1:-up}"
case "$cmd" in
  up|--build|--seed|"")
    build=0; do_seed=0
    for a in "$@"; do
      [[ "$a" == "--build" ]] && build=1
      [[ "$a" == "--seed" ]] && do_seed=1
    done
    up "$build" "$do_seed"
    ;;
  down)    echo "→ Останавливаю стек…"; $DC down; c_green "✓ остановлено (тома сохранены)";;
  restart) $DC restart; c_green "✓ перезапущено";;
  logs)    $DC logs -f --tail=100;;
  seed)    require_env; seed;;
  ps)      $DC ps;;
  *)       c_red "Неизвестная команда: $cmd"; sed -n '3,15p' "$0"; exit 1;;
esac
