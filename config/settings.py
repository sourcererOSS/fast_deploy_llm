"""Pydantic application settings (reads ``config/.env`` and OS environment)."""

from __future__ import annotations

import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from .env import ENV_FILE, ROOT_DIR, load_env

load_env()


class BackendSettings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=(str(ENV_FILE), str(ROOT_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    TITLE: str = "OpenAI-compatible Bedrock proxy"
    VERSION: str = "1.0.0"
    TIMEZONE: str = "UTC"
    DESCRIPTION: str | None = None
    DEBUG: bool = False

    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 4000
    SERVER_WORKERS: int = 1
    DOCS_URL: str = "/docs"
    OPENAPI_URL: str = "/openapi.json"
    REDOC_URL: str = "/redoc"
    OPENAPI_PREFIX: str = ""

    AWS_REGION: str = "ap-south-1"
    AWS_BEDROCK_API_KEY: str | None = None
    BEDROCK_ENDPOINT_API_KEY: str | None = None
    # X-Admin-Key / Bearer for /api/v1/admin/*. If unset, admin routes return 503.
    ADMIN_API_KEY: str | None = None

    IS_ALLOWED_CREDENTIALS: bool = True
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://0.0.0.0:3000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://0.0.0.0:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]
    ALLOWED_METHODS: list[str] = ["*"]
    ALLOWED_HEADERS: list[str] = ["*"]

    LOGGING_LEVEL: str = "info"
    LOGGERS: tuple[str, str] = ("uvicorn.asgi", "uvicorn.access")

    @property
    def set_backend_app_attributes(self) -> dict[str, str | bool | None]:
        return {
            "title": self.TITLE,
            "version": self.VERSION,
            "debug": self.DEBUG,
            "description": self.DESCRIPTION,
            "docs_url": self.DOCS_URL,
            "openapi_url": self.OPENAPI_URL,
            "redoc_url": self.REDOC_URL,
            "openapi_prefix": self.OPENAPI_PREFIX,
        }

    @property
    def logging_level_int(self) -> int:
        mapping = {
            "critical": logging.CRITICAL,
            "error": logging.ERROR,
            "warning": logging.WARNING,
            "info": logging.INFO,
            "debug": logging.DEBUG,
        }
        return mapping.get(self.LOGGING_LEVEL.lower(), logging.INFO)


@lru_cache
def get_settings() -> BackendSettings:
    return BackendSettings()


settings: BackendSettings = get_settings()
