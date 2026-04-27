# src/api/core/config/dev.py
from typing import List

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from .base import ApiSettings


class Settings(ApiSettings):
    """Development-specific settings that override base configuration"""

    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    LOG_USE_JSON: bool = False
    LOG_USE_COLORS: bool = True

    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        description="Allowed CORS origins for development",
    )

    CORS_ENABLED: bool = True
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Dev-specific config (e.g. different env file)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="BACKEND_",
        case_sensitive=True,
        extra="ignore",
        env_ignore_empty=True,
        env_file_optional=True,
    )
