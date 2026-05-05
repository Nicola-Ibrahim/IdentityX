from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SQLAlchemySettings(BaseSettings):
    """Configuration for SQLAlchemy engine and session factory."""

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        case_sensitive=False,
        extra="ignore",
    )

    url: str = Field(
        ...,
        description="Asynchronous database connection URL. Must start with 'postgresql+psycopg://'.",
    )
    echo: bool = Field(..., description="Whether to log SQL queries.", examples=[False, True])
    pool_size: int = Field(..., description="The size of the database pool.", examples=[5, 20])
    max_overflow: int = Field(..., description="The number of overflow connections.", examples=[10, 50])
    pool_pre_ping: bool = Field(..., description="Whether to test connections before use.", examples=[True])
    pool_recycle: int = Field(..., description="Connection recycle time in seconds.", examples=[3600])

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith("postgresql+psycopg://"):
            raise ValueError("SQLAlchemy URL must start with 'postgresql+psycopg://' for asynchronous operations.")
        return v


@lru_cache
def get_db_settings() -> SQLAlchemySettings:
    """
    Returns the SQLAlchemy settings.
    Caches the result for performance.
    """
    return SQLAlchemySettings()
