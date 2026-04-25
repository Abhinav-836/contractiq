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

    # Database - PostgreSQL for production
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/contractiq"

    # Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 50

    # LLM - Ollama Primary with GPT-OSS 20B
    LLM_PROVIDER: str = "ollama"
    
    # Ollama (Primary)
    OLLAMA_BASE_URL: str = "https://api.ollama.com"
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

    # Redis (optional)
    REDIS_URL: str = "redis://localhost:6379/0"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def effective_llm_provider(self) -> str:
        """Return the primary LLM provider"""
        return self.LLM_PROVIDER

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database"""
        return "sqlite" in self.DATABASE_URL

    def validate_required_secrets(self) -> List[str]:
        """Validate that required secrets are set in production"""
        missing = []
        if self.APP_ENV == "production":
            if self.SECRET_KEY == "dev-secret-change-in-production":
                missing.append("SECRET_KEY")
            if self.JWT_SECRET == "dev-jwt-secret-change-this":
                missing.append("JWT_SECRET")
        return missing

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

# Create upload dir on import
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Validate secrets in production
if settings.APP_ENV == "production":
    missing = settings.validate_required_secrets()
    if missing:
        raise ValueError(f"Missing required secrets in production: {', '.join(missing)}")