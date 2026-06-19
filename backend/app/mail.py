"""Отправка писем. backend/app/mail.py

Абстракция EmailSender + сменные реализации:
- ConsoleEmailSender — dev (письмо в лог)
- SmtpEmailSender — бой (реальная отправка, по умолчанию Яндекс smtp.yandex.ru:465)
Переключение — через settings.EMAIL_BACKEND (console | smtp), без правок логики.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from app.config import settings

logger = logging.getLogger(__name__)


class EmailSender(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> None: ...


class ConsoleEmailSender(EmailSender):
    """Dev-режим: письмо не уходит, а пишется в лог (ссылка видна в консоли)."""

    async def send(self, to: str, subject: str, body: str) -> None:
        logger.info(
            "\n===== EMAIL (console) =====\nTo: %s\nSubject: %s\n%s\n===========================",
            to, subject, body,
        )


class SmtpEmailSender(EmailSender):
    """Реальная отправка по SMTP. Дефолты — под Яндекс (smtp.yandex.ru).

    Порт 465 -> SSL сразу (use_tls). Порт 587 -> STARTTLS (start_tls).
    ВАЖНО (Яндекс): отправитель должен совпадать с ящиком, поэтому From = EMAIL_FROM
    или, если пусто, SMTP_USER. Пароль — ПАРОЛЬ ПРИЛОЖЕНИЯ Яндекса (не основной),
    при включённой двухфакторке. Кладётся только в .env.
    """

    async def send(self, to: str, subject: str, body: str) -> None:
        import aiosmtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["From"] = settings.EMAIL_FROM or settings.SMTP_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        use_ssl = settings.SMTP_PORT == 465
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=use_ssl,        # 465: SSL с самого начала
            start_tls=not use_ssl,  # 587: STARTTLS
            timeout=15,
        )
        logger.info("EMAIL (smtp) отправлено: to=%s subject=%s", to, subject)


def get_email_sender() -> EmailSender:
    if settings.EMAIL_BACKEND == "smtp":
        return SmtpEmailSender()
    return ConsoleEmailSender()


async def send_verification_email(to: str, code: str) -> None:
    body = (
        "Здравствуйте!\n\n"
        f"Ваш код подтверждения: {code}\n\n"
        f"Введите его на сайте. Код действует {settings.VERIFY_CODE_TTL_MINUTES} мин. "
        "Если вы не регистрировались — просто игнорируйте это письмо."
    )
    await get_email_sender().send(to, "Код подтверждения email", body)
