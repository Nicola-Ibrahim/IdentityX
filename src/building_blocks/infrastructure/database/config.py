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
        default="postgresql+psycopg://postgres:postgres@localhost:5432/identityx",
        description="Asynchronous database connection URL.",
    )
    echo: bool = Field(default=False, description="Whether to log SQL queries.")
    pool_size: int = Field(default=5, description="The size of the database pool.")
    max_overflow: int = Field(default=10, description="The number of overflow connections.")
    pool_pre_ping: bool = Field(default=True, description="Whether to test connections before use.")
    pool_recycle: int = Field(default=3600, description="Connection recycle time in seconds.")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith("postgresql+psycopg://"):
            raise ValueError("SQLAlchemy URL must start with 'postgresql+psycopg://' for asynchronous operations.")
        return v
