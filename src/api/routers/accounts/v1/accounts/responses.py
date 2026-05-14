from pydantic import BaseModel, EmailStr


class AccountResponse(BaseModel):
    id: str
    email: str
    is_verified: bool
    is_active: bool
    roles: list[str] = []


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    trusted_device_token: str | None = None


class MfaChallengeResponse(BaseModel):
    mfa_token: str
    mfa_setup_required: bool


class AuthResponse(BaseModel):
    requires_mfa: bool = False
    tokens: TokenResponse | None = None
    mfa: MfaChallengeResponse | None = None


class MfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    recovery_codes: list[str]


class SocialAuthUrlResponse(BaseModel):
    url: str
