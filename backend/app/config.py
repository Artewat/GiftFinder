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

    # Email-подтверждение (по 6-значному коду)
    EMAIL_BACKEND: str = "console"          # console | smtp (переключается через .env)
    EMAIL_FROM: str = ""                    # = адрес Яндекса (должен совпадать с SMTP_USER); пусто → берётся SMTP_USER
    VERIFY_CODE_LENGTH: int = 6
    VERIFY_CODE_TTL_MINUTES: int = 15       # код короткоживущий
    MAX_VERIFY_ATTEMPTS: int = 5            # защита от перебора кода
    RESEND_COOLDOWN_SECONDS: int = 60
    # SMTP (дефолты под Яндекс); реальные значения — в .env при EMAIL_BACKEND=smtp
    SMTP_HOST: str = "smtp.yandex.ru"
    SMTP_PORT: int = 465                     # 465 → SSL; 587 → STARTTLS
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""


settings = Settings()
