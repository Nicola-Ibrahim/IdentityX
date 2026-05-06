from pydantic import BaseModel


class TokenPair(BaseModel):
    """Access and Refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900
    trusted_device_token: str | None = None


class MfaChallenge(BaseModel):
    """MFA required challenge."""

    mfa_token: str
    mfa_setup_required: bool


class MfaSetup(BaseModel):
    """Data returned when initiating MFA setup."""

    secret: str
    provisioning_uri: str
    recovery_codes: list[str]


class AuthDTO(BaseModel):
    """
    Unified authentication result.
    """

    requires_mfa: bool = False
    tokens: TokenPair | None = None
    mfa: MfaChallenge | None = None
