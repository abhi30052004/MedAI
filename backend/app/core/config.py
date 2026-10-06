"""
Application configuration via pydantic-settings.
All secrets come from env / .env file.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────
    PROJECT_NAME: str = "MedAI API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:5173"

    # ── Database (Neon Postgres) ─────────────────────────────────
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/medai"
    DATABASE_URL_DIRECT: Optional[str] = None  # Non-pooled for Alembic

    # ── Auth / JWT ───────────────────────────────────────────────
    SECRET_KEY: str = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── AI Providers ─────────────────────────────────────────────
    PRIMARY_LLM_PROVIDER: str = "groq"
    FALLBACK_LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama3-70b-8192"

    # ── File Upload & Storage ────────────────────────────────────
    MAX_UPLOAD_MB: int = 25
    STORAGE_PATH: str = "./storage"
    FILE_ENCRYPTION_KEY: Optional[str] = None  # Fernet key, generated if missing

    # ── OCR ──────────────────────────────────────────────────────
    TESSERACT_CMD: str = "tesseract"
    OCR_DPI: int = 300

    # ── Worker ───────────────────────────────────────────────────
    AUTO_ANALYZE: bool = False

    # ── Email (SMTP) ─────────────────────────────────────────────
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "noreply@medai.local"
    SMTP_TLS: bool = True

    # ── Logging ──────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
