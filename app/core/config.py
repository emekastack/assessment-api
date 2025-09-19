import sys

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.logging import get_logger

logger = get_logger(__name__)

class Settings(BaseSettings):
    # --- Application Settings ---
    APP_ENV: str = "development"
    APP_PORT: int = 8004
    LOG_LEVEL: str = "INFO"
    
    # --- Redis Settings ---
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PRESENCE_TTL: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()