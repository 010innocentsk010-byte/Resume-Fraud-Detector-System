from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Noviq Intelligence"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    DATABASE_URL: str = "postgresql+psycopg2://resumefraud:resumefraud@localhost:5432/resumefraud"

    JWT_SECRET_KEY: str = "insecure-dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    STORAGE_BACKEND: str = "local"
    LOCAL_STORAGE_DIR: str = "./storage/resumes"
    MAX_UPLOAD_SIZE_MB: int = 10

    S3_BUCKET_NAME: str = ""
    S3_REGION: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_ENDPOINT_URL: str = ""

    SPACY_MODEL: str = "en_core_web_sm"
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"

    LOG_LEVEL: str = "INFO"

    # --- AI Rewrite Suggestions (Anthropic Claude) ---
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-5"
    ANTHROPIC_MAX_OUTPUT_TOKENS: int = 2000

    # --- Education Verification ---
    # Leave GHANA_EDU_API_KEY blank to skip the external lookup (falls back to
    # "pending" instead of erroring) — the provider contract below is UNVERIFIED,
    # confirm the real request/response shape before relying on it.
    GHANA_EDU_API_BASE_URL: str = "https://api.ghana.dev/api/v1/education"
    GHANA_EDU_API_KEY: str = ""
    GHANA_EDU_API_TIMEOUT_SECONDS: float = 5.0
    EDUCATION_VERIFY_RATE_LIMIT_PER_MINUTE: int = 20

    # --- Candidate Notification Email ---
    # Leave SMTP_HOST blank to skip sending — logs a warning instead of
    # failing the apply request. Works with any standard SMTP provider
    # (Gmail, SES, SendGrid, Mailgun, ...); no provider-specific SDK.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    EMAIL_FROM_ADDRESS: str = ""
    EMAIL_FROM_NAME: str = "Noviq Intelligence"

    # --- Public job-posting apply link (unauthenticated intake) ---
    PUBLIC_APPLY_RATE_LIMIT_PER_HOUR: int = 10
    PUBLIC_VIEW_RATE_LIMIT_PER_MINUTE: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
