from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://giftfinder:giftfinder@db:5432/giftfinder"

    nanogpt_api_key: str = "changeme"
    nanogpt_base_url: str = "https://nano-gpt.com/api/v1"
    nanogpt_model: str = "deepseek/deepseek-v3.2"

    embedding_model: str = "intfloat/multilingual-e5-base"

    media_dir: str = "media"

    # Аутентификация (этап 8)
    SECRET_KEY: str = "change-me-please-generate-a-long-random-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7   # неделя
    COOKIE_SECURE: bool = False                       # True в проде (HTTPS)
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # Email-подтверждение
    EMAIL_BACKEND: str = "console"          # console | smtp (smtp — точка расширения)
    EMAIL_FROM: str = "no-reply@giftfinder.local"
    VERIFY_TOKEN_TTL_HOURS: int = 24
    RESEND_COOLDOWN_SECONDS: int = 60
    # для будущего SMTP (пока не используются):
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""


settings = Settings()
