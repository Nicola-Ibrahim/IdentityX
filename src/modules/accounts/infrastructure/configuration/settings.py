from pydantic_settings import BaseSettings, SettingsConfigDict


class AccountsSettings(BaseSettings):
    """Configuration for the Accounts bounded context."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="BACKEND_ACCOUNTS_",
        case_sensitive=True,
        extra="ignore",
        env_ignore_empty=True,
        env_file_optional=True,
    )

    ENABLE_REGISTRATION: bool = True
    DEFAULT_ROLE: str = "user"
    
    # JWT / RS256
    JWT_ALGORITHM: str = "RS256"
    JWT_PRIVATE_KEY: str = ""
    JWT_PUBLIC_KEY: str = ""
    JWT_ISSUER: str = "identityx"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
