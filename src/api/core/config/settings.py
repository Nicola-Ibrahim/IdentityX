import logging.config
from typing import Any, List

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Main application settings.
    All values can be overridden via environment variables with 'BACKEND_' prefix.
    Example: BACKEND_DEBUG=True
    """

    # Pydantic v2-style config
    model_config = SettingsConfigDict(
        env_prefix="BACKEND_",
        case_sensitive=True,
        extra="ignore",
        env_ignore_empty=True,
    )

    # --- Application Metadata ---
    PROJECT_NAME: str = Field(..., description="Project name", examples=["IdentityX"])
    VERSION: str = Field(..., description="Application version", examples=["1.0.0"])
    DESCRIPTION: str = Field(
        ..., description="API description", examples=["Modern OAuth2 / Identity Provider service."]
    )
    ENVIRONMENT: str = Field(..., description="Current environment", examples=["development", "production", "testing"])

    # --- Server Config ---
    HOST: str = Field(..., description="Binding host", examples=["0.0.0.0"])
    PORT: int = Field(..., description="Binding port", examples=[8000])
    WORKERS: int = Field(..., description="Number of uvicorn workers", examples=[1, 4])
    API_VERSION: str = Field(..., description="Main API version prefix", examples=["v1"])

    # --- Security ---
    SECRET_KEY: str = Field(
        ...,
        description="Secret key for crypto operations. MUST be set in environment.",
        examples=["your-ultra-secret-key"],
    )
    CORS_ENABLED: bool = Field(..., description="Enable CORS middleware", examples=[True])
    CORS_ORIGINS: List[AnyHttpUrl | str] = Field(
        ..., description="Allowed CORS origins", examples=[["*"], ["https://example.com"]]
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(..., description="Allow credentials in CORS requests", examples=[True])
    CORS_ALLOW_METHODS: List[str] = Field(..., description="Allowed CORS methods", examples=[["*"], ["GET", "POST"]])
    CORS_ALLOW_HEADERS: List[str] = Field(
        ..., description="Allowed CORS headers", examples=[["*"], ["Content-Type", "Authorization"]]
    )

    # --- Logging ---
    LOGGER_NAME: str = Field(..., description="Main logger name", examples=["identityx"])
    LOG_LEVEL: str = Field(..., description="Global log level", examples=["INFO", "DEBUG", "ERROR"])
    LOG_FORMAT: str = Field(..., description="Log message format", examples=["%(levelprefix)s | %(message)s"])
    LOG_DATEFMT: str = Field(..., description="Log date format", examples=["%Y-%m-%d %H:%M:%S"])
    LOG_USE_COLORS: bool = Field(..., description="Enable colored logs", examples=[True])
    LOG_USE_JSON: bool = Field(..., description="Enable JSON logging for production", examples=[False])

    @property
    def DEBUG(self) -> bool:
        """Automatically enable debug mode in development environment."""
        return self.ENVIRONMENT.lower() in ("development", "dev")

    def configure(self) -> None:
        """Apply all configurations (logging, etc.)."""
        log_level = "DEBUG" if self.DEBUG else self.LOG_LEVEL
        logging.config.dictConfig(self.logging_dict_config(log_level))

    def logging_dict_config(self, log_level: str) -> dict[str, Any]:
        """Return a streamlined, production-grade logging configuration."""
        handler_name = "json_console" if self.LOG_USE_JSON else "console"

        # Standard formatters
        formatters = {
            "standard": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": self.LOG_FORMAT,
                "datefmt": self.LOG_DATEFMT,
                "use_colors": self.LOG_USE_COLORS,
            },
        }

        # Handlers
        handlers = {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
        }

        # Optional JSON Handler
        if self.LOG_USE_JSON:
            try:
                import pythonjsonlogger.jsonlogger  # noqa: F401

                formatters["json"] = {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "fmt": "%(asctime)s %(name)s %(levelname)s %(message)s",
                }
                handlers["json_console"] = {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "stream": "ext://sys.stdout",
                }
            except ImportError:
                handler_name = "console"

        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": formatters,
            "handlers": handlers,
            "loggers": {
                # Root logger captures everything from 3rd party libs
                "": {"handlers": [handler_name], "level": "INFO"},
                # App-specific logger
                self.LOGGER_NAME: {"level": log_level, "propagate": True},
                # Detailed Uvicorn loggers
                "uvicorn.error": {"level": "INFO", "propagate": True},
                "uvicorn.access": {"level": "INFO", "propagate": True},
                # Database logger (shows SQL if level is DEBUG)
                "sqlalchemy.engine": {"level": log_level, "propagate": True},
            },
        }
