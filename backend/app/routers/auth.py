"""Роуты аутентификации. backend/app/routers/auth.py
Подключи в main.py:  app.include_router(auth_router)

Модель регистрации: пользователь попадает в `users` ТОЛЬКО после подтверждения
почты. До этого заявка живёт в `pending_registrations`; письмо с кодом шлётся ДО
сохранения, поэтому сбой SMTP не оставляет «призраков» в БД.
"""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select

from app.auth import (
    COOKIE_NAME, create_access_token, get_current_user,
    hash_password, verify_password,
)
from app.config import settings
from app.db import async_session
from app.mail import send_verification_email
from app.models import PendingRegistration, User
from app.schemas import EmailIn, LoginRequest, UserCreate, UserOut, VerifyCode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _generate_code() -> str:
    """6-значный (по настройке) числовой код подтверждения."""
    return "".join(secrets.choice("0123456789") for _ in range(settings.VERIFY_CODE_LENGTH))


def _code_expiry() -> datetime:
    return _now() + timedelta(minutes=settings.VERIFY_CODE_TTL_MINUTES)


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,   # False на localhost (http), True в проде
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate):
    async with async_session() as session:
        # уже подтверждённый пользователь?
        exists = await session.execute(select(User).where(User.email == data.email))
        if exists.scalar_one_or_none() is not None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email уже зарегистрирован")

        pres = await session.execute(
            select(PendingRegistration).where(PendingRegistration.email == data.email)
        )
        pending = pres.scalar_one_or_none()
        # свежая заявка в пределах кулдауна — код ещё жив, повторно не шлём (анти-спам)
        if pending is not None and (_now() - pending.created_at).total_seconds() < settings.RESEND_COOLDOWN_SECONDS:
            return {"status": "verification_sent", "email": data.email}

        code = _generate_code()
        # ПИСЬМО ДО записи в БД: упал SMTP -> ничего не сохраняем, чистый повтор
        try:
            await send_verification_email(data.email, code)
        except Exception as exc:  # noqa: BLE001 — любой сбой доставки = регистрация не состоялась
            logger.warning("register: письмо не отправлено (to=%s): %s", data.email, exc)
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "Не удалось отправить письмо с кодом. Проверьте адрес и попробуйте позже.",
            )

        if pending is None:
            session.add(PendingRegistration(
                email=data.email,
                password_hash=hash_password(data.password),
                code=code,
                expires_at=_code_expiry(),
            ))
        else:  # перерегистрация того же email до подтверждения — обновляем заявку
            pending.password_hash = hash_password(data.password)
            pending.code = code
            pending.attempts = 0
            pending.expires_at = _code_expiry()
            pending.created_at = _now()
        await session.commit()
    return {"status": "verification_sent", "email": data.email}


@router.post("/login", response_model=UserOut)
async def login(data: LoginRequest, response: Response):
    async with async_session() as session:
        res = await session.execute(select(User).where(User.email == data.email))
        user = res.scalar_one_or_none()
        # неподтверждённых в `users` нет -> простая проверка пароля
        if user is None or not verify_password(data.password, user.password_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неверный email или пароль")
        _set_auth_cookie(response, create_access_token(str(user.id)))
        return user


@router.post("/verify-email", response_model=UserOut)
async def verify_email(data: VerifyCode, response: Response):
    async with async_session() as session:
        # уже полноценный пользователь?
        ures = await session.execute(select(User).where(User.email == data.email))
        if ures.scalar_one_or_none() is not None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email уже подтверждён, войдите")

        pres = await session.execute(
            select(PendingRegistration).where(PendingRegistration.email == data.email)
        )
        pending = pres.scalar_one_or_none()
        if pending is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                "Регистрация не начата или код истёк. Зарегистрируйтесь заново.")
        if pending.expires_at < _now():
            await session.delete(pending)
            await session.commit()
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Код истёк. Зарегистрируйтесь заново.")
        if pending.attempts >= settings.MAX_VERIFY_ATTEMPTS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                "Слишком много попыток. Зарегистрируйтесь заново.")
        if not secrets.compare_digest(pending.code, (data.code or "").strip()):
            pending.attempts += 1
            await session.commit()
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Неверный код")

        # код верный -> заявка превращается в настоящего пользователя
        user = User(
            email=pending.email,
            password_hash=pending.password_hash,
            tier="free",
            email_verified=True,
        )
        session.add(user)
        await session.delete(pending)
        await session.commit()
        await session.refresh(user)
        # есть доступ к почте -> сразу логиним
        _set_auth_cookie(response, create_access_token(str(user.id)))
        return user


@router.post("/resend-verification")
async def resend_verification(data: EmailIn):
    # Единый ответ независимо от существования заявки — без утечки базы пользователей.
    async with async_session() as session:
        pres = await session.execute(
            select(PendingRegistration).where(PendingRegistration.email == data.email)
        )
        pending = pres.scalar_one_or_none()
        if pending is not None and (_now() - pending.created_at).total_seconds() >= settings.RESEND_COOLDOWN_SECONDS:
            code = _generate_code()
            try:
                await send_verification_email(pending.email, code)
            except Exception as exc:  # noqa: BLE001
                logger.warning("resend: письмо не отправлено (to=%s): %s", pending.email, exc)
            else:  # обновляем код только если письмо реально ушло (старый код остаётся валиден)
                pending.code = code
                pending.attempts = 0
                pending.expires_at = _code_expiry()
                pending.created_at = _now()
                await session.commit()
    return {"status": "ok",
            "message": "Если регистрация начата и не подтверждена, код отправлен"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"status": "ok"}


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
