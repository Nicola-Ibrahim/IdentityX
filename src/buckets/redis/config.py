from pydantic import Field, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    """Configuration for Redis infrastructure."""

    model_config = SettingsConfigDict(
        env_prefix="BACKEND_",
        case_sensitive=True,
        extra="ignore",
    )

    REDIS_URL: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for rate limiting, caching, and background tasks"
    )
    
    REDIS_MAX_CONNECTIONS: int = Field(default=10, description="Maximum number of connections in the pool")
    REDIS_SOCKET_TIMEOUT: float = Field(default=5.0, description="Socket timeout in seconds")
    REDIS_HEALTH_CHECK_INTERVAL: int = Field(default=30, description="Interval in seconds to perform health checks")


def get_redis_settings() -> RedisSettings:
    return RedisSettings()
