"""
Piranha Configuration
Centralizes all environment variables and settings using Pydantic Settings.
"""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql://piranha:pass@localhost:5432/piranha"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT Auth
    secret_key: str = "CHANGE_ME_IN_PRODUCTION_USE_OPENSSL_RAND"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    
    # ML Model
    model_path: str = "/models"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # App
    debug: bool = False
    app_name: str = "Piranha ITA"
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance.
    Use dependency injection in FastAPI routes.
    """
    return Settings()
