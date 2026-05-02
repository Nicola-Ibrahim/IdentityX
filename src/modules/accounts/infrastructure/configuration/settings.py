from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AccountsSettings(BaseSettings):
    """Configuration for the Accounts bounded context."""

    model_config = SettingsConfigDict(
        env_prefix="BACKEND_",
        case_sensitive=True,
        extra="ignore",
        env_ignore_empty=True,
    )

    ENABLE_REGISTRATION: bool = Field(..., description="Enable account registration", examples=[True])
    DEFAULT_ROLE: str = Field(..., description="Default role for new accounts", examples=["user"])

    # JWT / RS256
    JWT_ALGORITHM: str = Field(..., description="JWT signing algorithm", examples=["RS256"])
    JWT_PRIVATE_KEY: str = Field(
        ...,
        description="RSA Private Key for token signing. MUST be set in environment.",
        examples=["-----BEGIN RSA PRIVATE KEY-----..."],
    )
    JWT_PUBLIC_KEY: str = Field(
        ...,
        description="RSA Public Key for token verification. MUST be set in environment.",
        examples=["-----BEGIN PUBLIC KEY-----..."],
    )
    JWT_ISSUER: str = Field(..., description="JWT issuer claim", examples=["identityx"])
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(..., description="Access token TTL", examples=[15, 60])
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(..., description="Refresh token TTL", examples=[7, 30])
