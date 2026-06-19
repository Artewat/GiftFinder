from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SearchRequest(BaseModel):
    query: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyToken(BaseModel):
    token: str


class EmailIn(BaseModel):
    email: EmailStr


class UserOut(BaseModel):
    id: int
    email: EmailStr
    tier: str
    email_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UsageOut(BaseModel):
    tier: str
    limit: int | None      # null для premium (безлимит)
    used: int
    remaining: int | None  # null для premium


class WishlistAdd(BaseModel):
    product_id: int


class WishlistItemOut(BaseModel):
    id: int
    product_id: int | None
    available: bool
    title: str
    price: float | None
    currency: str
    image_url: str | None
    product_url: str
    added_at: datetime


class GiftCard(BaseModel):
    id: int
    title: str
    price: float | None
    currency: str
    image_url: str | None
    product_url: str
    source: str
    reason: str | None


class SearchResponse(BaseModel):
    results: list[GiftCard]


class HealthResponse(BaseModel):
    status: str
    database: str
