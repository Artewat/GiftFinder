"""Отправка писем. backend/app/mail.py

Абстракция EmailSender + сменные реализации. Сейчас активна ConsoleEmailSender
(письмо печатается в лог backend). SMTP — помеченная точка расширения:
подключается одним классом + переключением EMAIL_BACKEND, без правок логики.
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


# Точка расширения. Подключить: pip install aiosmtplib, EMAIL_BACKEND=smtp,
# заполнить SMTP_* в .env, раскомментировать и вернуть в get_email_sender().
#
# class SmtpEmailSender(EmailSender):
#     async def send(self, to: str, subject: str, body: str) -> None:
#         import aiosmtplib
#         from email.message import EmailMessage
#         msg = EmailMessage()
#         msg["From"] = settings.EMAIL_FROM
#         msg["To"] = to
#         msg["Subject"] = subject
#         msg.set_content(body)
#         await aiosmtplib.send(
#             msg, hostname=settings.SMTP_HOST, port=settings.SMTP_PORT,
#             username=settings.SMTP_USER, password=settings.SMTP_PASSWORD,
#             start_tls=True,
#         )


def get_email_sender() -> EmailSender:
    if settings.EMAIL_BACKEND == "smtp":
        raise NotImplementedError(
            "SMTP-отправка — точка расширения; пока активен EMAIL_BACKEND=console"
        )
    return ConsoleEmailSender()


def verification_link(token: str) -> str:
    return f"{settings.FRONTEND_ORIGIN}/verify-email?token={token}"


async def send_verification_email(to: str, token: str) -> None:
    link = verification_link(token)
    body = (
        "Здравствуйте!\n\n"
        "Подтвердите ваш email, перейдя по ссылке:\n"
        f"{link}\n\n"
        f"Ссылка действует {settings.VERIFY_TOKEN_TTL_HOURS} ч. "
        "Если вы не регистрировались — просто игнорируйте это письмо."
    )
    await get_email_sender().send(to, "Подтверждение email", body)
