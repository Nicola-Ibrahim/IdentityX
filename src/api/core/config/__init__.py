from functools import lru_cache

from src.api.core.config.settings import Settings


@lru_cache
def get_settings() -> Settings:
    """
    Returns the application settings.
    Caches the result for performance.
    """
    return Settings()
