import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "TradingOS"
    DEBUG: bool = True
    VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@192.168.31.132:5432/tradingos"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://192.168.31.132:6379/0"

    # Data Collection
    REALTIME_INTERVAL: int = 5
    MINUTE_INTERVAL: int = 60
    DAILY_SCHEDULE: str = "18:00"

    # Data Sources
    AKSHARE_ENABLED: bool = True

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = str(Path(__file__).parent / ".env")
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
