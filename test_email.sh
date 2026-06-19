#!/usr/bin/env bash
# Тест реальной отправки email через SMTP (Яндекс).
# Запускать ПОД включённым VPN, у которого открыт доступ к smtp.yandex.ru:465.
#
#   ./test_email.sh                 # письмо на адрес из SMTP_USER (.env)
#   ./test_email.sh you@yandex.ru   # письмо на указанный адрес
#
# Что делает: проверяет TCP-доступность 465/587 из контейнера backend,
# показывает SMTP-настройки (пароль маскирует) и шлёт тестовое письмо.

set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

# docker compose (v2) или docker-compose (v1)
if docker compose version >/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
else
  echo "✗ Не найден docker compose / docker-compose" >&2
  exit 1
fi

TO="${1:-}"

green() { printf '\033[32m%s\033[0m\n' "$1"; }
red()   { printf '\033[31m%s\033[0m\n' "$1"; }
yellow(){ printf '\033[33m%s\033[0m\n' "$1"; }

# backend поднят?
if ! $DC ps --status running 2>/dev/null | grep -q backend; then
  yellow "Backend не запущен — поднимаю…"
  $DC up -d backend >/dev/null
  sleep 3
fi

echo "──────────────────────────────────────────────"
echo "1) Настройки SMTP (из .env, как их видит backend)"
echo "──────────────────────────────────────────────"
$DC exec -T backend python -c "
from app.config import settings
print('EMAIL_BACKEND =', settings.EMAIL_BACKEND)
print('SMTP_HOST     =', settings.SMTP_HOST)
print('SMTP_PORT     =', settings.SMTP_PORT)
print('SMTP_USER     =', settings.SMTP_USER)
print('EMAIL_FROM    =', settings.EMAIL_FROM or '(пусто → возьмётся SMTP_USER)')
print('PASSWORD set  =', bool(settings.SMTP_PASSWORD))
print('BACKEND_OK    =', settings.EMAIL_BACKEND == 'smtp')
"

if [ "$($DC exec -T backend python -c 'from app.config import settings; print(settings.EMAIL_BACKEND)' | tr -d '\r')" != "smtp" ]; then
  red "✗ EMAIL_BACKEND != smtp — в .env поставь EMAIL_BACKEND=smtp и перезапусти backend (./start.sh restart)."
  exit 1
fi

echo ""
echo "──────────────────────────────────────────────"
echo "2) Доступность Яндекс-SMTP из контейнера (нужен VPN)"
echo "──────────────────────────────────────────────"
$DC exec -T backend python -c "
import socket
ok = False
for port in (465, 587):
    s = socket.socket(); s.settimeout(8)
    try:
        s.connect(('smtp.yandex.ru', port)); print(f'  port {port}: OPEN'); ok = True
    except Exception as e:
        print(f'  port {port}: {type(e).__name__} ({e})')
    finally:
        s.close()
import sys
sys.exit(0 if ok else 2)
" || { red "✗ Оба порта закрыты — VPN не туннелирует smtp.yandex.ru (77.88.21.0/24). Включи туннель и повтори."; exit 2; }

echo ""
echo "──────────────────────────────────────────────"
echo "3) Реальная отправка тестового письма"
echo "──────────────────────────────────────────────"
# адрес получателя: аргумент или SMTP_USER
if [ -z "$TO" ]; then
  TO="$($DC exec -T backend python -c 'from app.config import settings; print(settings.SMTP_USER)' | tr -d '\r')"
fi
echo "  Получатель: $TO"

if $DC exec -T backend python -c "
import asyncio
from app.mail import send_verification_email
asyncio.run(send_verification_email('$TO', 'TESTTOKEN123'))
print('  send() завершился без ошибок')
"; then
  green "✓ Письмо отправлено. Проверь ящик $TO (и папку «Спам»)."
  echo "  Ожидай письмо «Подтверждение email» со ссылкой /verify-email?token=TESTTOKEN123"
else
  red "✗ Отправка упала. Частые причины:"
  echo "   • неверный пароль приложения (не основной пароль Яндекса);"
  echo "   • двухфакторка/пароли приложений не включены в Яндекс ID;"
  echo "   • VPN отвалился во время отправки."
  exit 1
fi
