from pydantic import BaseModel


class AccountResponse(BaseModel):
    """Public representation of an account."""

    id: str
    email: str
    is_verified: bool
    is_active: bool
    roles: list[str]


class TokenResponse(BaseModel):
    """Response schema for authentication tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    trusted_device_token: str | None = None


class MfaChallengeResponse(BaseModel):
    """Response schema for MFA challenge."""

    mfa_token: str
    mfa_setup_required: bool


class AuthResponse(BaseModel):
    """Combined authentication result."""

    requires_mfa: bool = False
    tokens: TokenResponse | None = None
    mfa: MfaChallengeResponse | None = None


class MfaSetupResponse(BaseModel):
    """Response schema for MFA setup information."""

    secret: str
    provisioning_uri: str
    recovery_codes: list[str]


class SocialAuthUrlResponse(BaseModel):
    """Response schema for social login URL."""

    url: str
