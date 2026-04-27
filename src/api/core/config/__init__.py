import os
from functools import lru_cache
from importlib import import_module

from .base import ApiSettings


@lru_cache
def get_settings() -> ApiSettings:
    """
    Dynamically loads the appropriate settings module based on environment.
    Caches the result for performance.
    """
    env = os.getenv("BACKEND_ENVIRONMENT", "dev").lower()

    # __name__ is 'src.api.core.config' when this function is in config/__init__.py
    base_package = __name__  # e.g. "src.api.core.config"
    module_path = f"{base_package}.{env}"  # e.g. "src.api.core.config.dev"

    try:
        settings_module = import_module(module_path)
        if not hasattr(settings_module, "Settings"):
            raise AttributeError(f"Module '{module_path}' does not define a 'Settings' class")
        return settings_module.Settings()
    except Exception as exc:
        raise ImportError(
            f"Could not import settings for environment '{env}'. Expected module '{module_path}'"
        ) from exc
