import logging.config
from typing import Any

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    """Main application settings with environment-aware configuration"""

    # Pydantic v2-style config
    model_config = SettingsConfigDict(
        env_prefix="BACKEND_",
        case_sensitive=True,
        extra="ignore",
        env_ignore_empty=True,
    )

    # Application Metadata
    PROJECT_NAME: str = "IdentityX"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    DESCRIPTION: str = "Modern OAuth2 / Identity Provider service."
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    API_VERSION: str = "v1"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] | list[str] = []
    CORS_ENABLED: bool = True
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # Logging defaults (overridable per environment)
    LOGGER_NAME: str = "identityx"
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(name)s | %(message)s"
    LOG_DATEFMT: str = "%Y-%m-%d %H:%M:%S"
    LOG_USE_COLORS: bool = True
    LOG_USE_JSON: bool = False

    def configure(self) -> None:
        """Apply all configurations"""
        log_level = "DEBUG" if self.DEBUG else self.LOG_LEVEL
        logging.config.dictConfig(self.logging_dict_config(log_level))

    def logging_dict_config(self, log_level: str) -> dict[str, Any]:
        """Return dictConfig ready logging configuration for the environment."""
        handler_name = "json_console" if self.LOG_USE_JSON else "console"

        formatters = {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": self.LOG_FORMAT,
                "datefmt": self.LOG_DATEFMT,
                "use_colors": self.LOG_USE_COLORS,
            },
        }
        handlers = {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        }

        if self.LOG_USE_JSON:
            formatters["json"] = {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "fmt": self.LOG_FORMAT,
            }
            handlers["json_console"] = {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": "ext://sys.stdout",
            }

        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": formatters,
            "handlers": handlers,
            "loggers": {
                self.LOGGER_NAME: {
                    "handlers": [handler_name],
                    "level": log_level,
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": [handler_name],
                    "level": "INFO",
                    "propagate": False,
                },
            },
        }
