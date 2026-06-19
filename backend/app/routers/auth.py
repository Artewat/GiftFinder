"""Роуты аутентификации. backend/app/routers/auth.py
Подключи в main.py:  app.include_router(auth_router)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select

from app.auth import (
    COOKIE_NAME, create_access_token, get_current_user,
    hash_password, verify_password,
)
from app.config import settings
from app.db import async_session
from app.models import User
from app.schemas import LoginRequest, UserCreate, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


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


@router.post("/register", response_model=UserOut)
async def register(data: UserCreate, response: Response):
    async with async_session() as session:
        exists = await session.execute(select(User).where(User.email == data.email))
        if exists.scalar_one_or_none() is not None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email уже зарегистрирован")
        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            tier="free",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    _set_auth_cookie(response, create_access_token(str(user.id)))
    return user


@router.post("/login", response_model=UserOut)
async def login(data: LoginRequest, response: Response):
    async with async_session() as session:
        res = await session.execute(select(User).where(User.email == data.email))
        user = res.scalar_one_or_none()
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неверный email или пароль")
    _set_auth_cookie(response, create_access_token(str(user.id)))
    return user


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"status": "ok"}


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
