from functools import lru_cache
from .settings import Settings


@lru_cache
def get_settings() -> Settings:
    """
    Returns the application settings.
    Caches the result for performance.
    """
    return Settings()
