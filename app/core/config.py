from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    log_level: str = "INFO"
    librarr_cloud_url: str = "https://api.librarr.com/v1"
    database_url: str = "postgresql+asyncpg://librarr:librarr@localhost:5432/librarr"
    redis_url: str = "redis://localhost:6379/0"


settings = Settings()
