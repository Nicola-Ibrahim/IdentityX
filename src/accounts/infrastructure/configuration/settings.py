from pydantic import Field, HttpUrl
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

    # Google OAuth2
    GOOGLE_CLIENT_ID: str = Field(..., description="Google OAuth2 Client ID")
    GOOGLE_CLIENT_SECRET: str = Field(..., description="Google OAuth2 Client Secret")
    GOOGLE_REDIRECT_URI: HttpUrl = Field(..., description="Google OAuth2 Redirect URI")
    GOOGLE_AUTH_URL: HttpUrl = Field(
        ..., description="Google OAuth2 Authorization URL", examples=["https://accounts.google.com/o/oauth2/v2/auth"]
    )
    GOOGLE_METADATA_URL: HttpUrl = Field(
        ...,
        description="Google OAuth2 Metadata URL",
        examples=["https://accounts.google.com/.well-known/openid-configuration"],
    )

    # MFA
    MFA_ISSUER_NAME: str = Field(..., description="MFA Issuer Name", examples=["IdentityX"])

    # Trusted Devices
    TRUSTED_DEVICE_TTL_DAYS: int = Field(..., description="Trusted Device TTL in days", examples=[30])
