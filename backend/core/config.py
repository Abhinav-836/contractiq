# core/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ContractIQ"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-change-in-production"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Database - SQLite for dev, Postgres for prod
    DATABASE_URL: str = "sqlite+aiosqlite:///./contractiq.db"

    # Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 20

    # LLM - Ollama Cloud Primary with GPT-OSS 20B
    LLM_PROVIDER: str = "ollama"

    # Ollama Cloud
    OLLAMA_BASE_URL: str = "https://ollama.com"
    OLLAMA_MODEL: str = "gpt-oss:20b"
    OLLAMA_API_KEY: Optional[str] = None
    OLLAMA_IS_CLOUD: bool = True

    # Gemini (First Fallback)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # OpenAI (Second Fallback)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # JWT
    JWT_SECRET: str = "dev-jwt-secret-change-this"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080

    # Google sign-in: the OAuth "Web application" client ID from Google Cloud
    # (ends in .apps.googleusercontent.com). Empty = the Google button is hidden.
    GOOGLE_CLIENT_ID: Optional[str] = None

    # Create test@example.com / test1234 on an empty DB (local dev only)
    SEED_DEV_USER: bool = False

    # Redis (optional)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Email. Render's free plan blocks SMTP ports, so mail goes through an
    # email service's HTTPS API. "none" (default) sends nothing; "console"
    # logs instead of sending (local dev); "brevo" or "resend" send for real.
    EMAIL_PROVIDER: str = "none"
    EMAIL_FROM: Optional[str] = None          # verified sender, e.g. you@gmail.com (Brevo) or noreply@yourdomain.com (Resend)
    EMAIL_FROM_NAME: str = "ContractIQ"
    BREVO_API_KEY: Optional[str] = None
    RESEND_API_KEY: Optional[str] = None
    # Public address of the frontend, used for links in emails.
    # Defaults to the first https origin in ALLOWED_ORIGINS.
    APP_URL: Optional[str] = None
    # Brevo's free plan allows 300 emails a day; stay under it, and stop one
    # workspace from using ContractIQ to spam people.
    EMAIL_DAILY_LIMIT: int = 280
    EMAIL_DAILY_LIMIT_PER_WORKSPACE: int = 100

    # AI review limits per rolling 24 hours (0 = no limit). See modules/usage/service.py
    AI_REVIEWS_PER_USER_DAILY: int = 5
    AI_REVIEWS_DAILY_TOTAL: int = 200

    @property
    def allowed_origins_list(self) -> List[str]:
        # A trailing slash ("https://app.vercel.app/") never matches the browser's
        # Origin header and silently breaks CORS — normalize it away.
        return [o.strip().rstrip("/") for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def app_url(self) -> str:
        if self.APP_URL:
            return self.APP_URL.rstrip("/")
        origins = self.allowed_origins_list
        return next((o for o in origins if o.startswith("https://")), origins[0] if origins else "http://localhost:3000")

    @property
    def email_enabled(self) -> bool:
        provider = (self.EMAIL_PROVIDER or "none").lower()
        if provider == "console":
            return True
        if provider == "brevo":
            return bool(self.BREVO_API_KEY and self.EMAIL_FROM)
        if provider == "resend":
            return bool(self.RESEND_API_KEY and self.EMAIL_FROM)
        return False

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def effective_llm_provider(self) -> str:
        return self.LLM_PROVIDER

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    def validate_required_secrets(self) -> List[str]:
        missing = []
        if self.APP_ENV == "production":
            if self.SECRET_KEY == "dev-secret-change-in-production":
                missing.append("SECRET_KEY")
            if self.JWT_SECRET == "dev-jwt-secret-change-this":
                missing.append("JWT_SECRET")
            if self.LLM_PROVIDER == "ollama" and not self.OLLAMA_API_KEY:
                missing.append("OLLAMA_API_KEY (required when LLM_PROVIDER=ollama)")
        return missing

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

if settings.APP_ENV == "production":
    _missing = settings.validate_required_secrets()
    if _missing:
        raise ValueError(f"Missing required secrets in production: {', '.join(_missing)}")