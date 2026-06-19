"""Роуты аутентификации. backend/app/routers/auth.py
Подключи в main.py:  app.include_router(auth_router)
"""
from __future__ import annotations

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
from app.models import EmailVerificationToken, User
from app.schemas import EmailIn, LoginRequest, UserCreate, UserOut, VerifyToken

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _create_token(session, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    session.add(EmailVerificationToken(
        user_id=user_id,
        token=token,
        expires_at=_now() + timedelta(hours=settings.VERIFY_TOKEN_TTL_HOURS),
    ))
    await session.commit()
    return token


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
        exists = await session.execute(select(User).where(User.email == data.email))
        if exists.scalar_one_or_none() is not None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email уже зарегистрирован")
        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            tier="free",
            email_verified=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        token = await _create_token(session, user.id)
    # строгий режим: куку НЕ ставим — вход только после подтверждения
    await send_verification_email(user.email, token)
    return {"status": "ok", "message": "Письмо для подтверждения отправлено"}


@router.post("/login", response_model=UserOut)
async def login(data: LoginRequest, response: Response):
    async with async_session() as session:
        res = await session.execute(select(User).where(User.email == data.email))
        user = res.scalar_one_or_none()
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неверный email или пароль")
    if not user.email_verified:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Email не подтверждён. Проверьте почту или запросите письмо повторно.",
        )
    _set_auth_cookie(response, create_access_token(str(user.id)))
    return user


@router.post("/verify-email")
async def verify_email(data: VerifyToken):
    async with async_session() as session:
        res = await session.execute(
            select(EmailVerificationToken).where(EmailVerificationToken.token == data.token)
        )
        tok = res.scalar_one_or_none()
        if tok is None or tok.used_at is not None or tok.expires_at < _now():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ссылка недействительна или истекла")
        user = await session.get(User, tok.user_id)
        user.email_verified = True
        tok.used_at = _now()
        await session.commit()
    return {"status": "ok", "message": "Email подтверждён"}


@router.post("/resend-verification")
async def resend_verification(data: EmailIn):
    # Единый ответ независимо от существования адреса — без утечки базы пользователей.
    async with async_session() as session:
        res = await session.execute(select(User).where(User.email == data.email))
        user = res.scalar_one_or_none()
        if user is not None and not user.email_verified:
            last = await session.execute(
                select(EmailVerificationToken.created_at)
                .where(EmailVerificationToken.user_id == user.id)
                .order_by(EmailVerificationToken.created_at.desc())
                .limit(1)
            )
            last_at = last.scalar_one_or_none()
            cooldown = settings.RESEND_COOLDOWN_SECONDS
            if last_at is None or (_now() - last_at).total_seconds() >= cooldown:
                token = await _create_token(session, user.id)
                await send_verification_email(user.email, token)
    return {"status": "ok",
            "message": "Если адрес зарегистрирован и не подтверждён, письмо отправлено"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"status": "ok"}


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
