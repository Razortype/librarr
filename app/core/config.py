from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://librarr:librarr@localhost:5432/librarr"
    redis_url: str = "redis://localhost:6379/0"
    # Cloud: empty key disables cloud enrichment; set to enable
    librarr_cloud_url: str = "https://api.librarr.com/v1"
    librarr_cloud_api_key: str = ""
    # Open Library
    openlibrary_base_url: str = "https://openlibrary.org"
    # Prowlarr indexer manager
    prowlarr_url: str = "http://localhost:9696"
    prowlarr_api_key: str = ""
    # HTTP timeouts (seconds)
    http_timeout_connect: float = 5.0
    http_timeout_read: float = 10.0
    cloud_timeout_read: float = 4.5  # leaves budget for service-layer 5s fallback
    # CORS
    cors_allow_origins: list[str] = ["http://localhost:5100", "http://localhost:3000"]


settings = Settings()
