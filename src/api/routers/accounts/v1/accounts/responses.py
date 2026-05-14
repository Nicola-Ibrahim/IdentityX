from pydantic import BaseModel
from typing import List, Optional


class AccountResponse(BaseModel):
    """Public representation of an account."""
    id: str
    email: str
    is_verified: bool
    is_active: bool
    roles: List[str]


class TokenResponse(BaseModel):
    """Response schema for authentication tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    trusted_device_token: Optional[str] = None


class MfaChallengeResponse(BaseModel):
    """Response schema for MFA challenge."""
    mfa_token: str
    mfa_setup_required: bool


class AuthResponse(BaseModel):
    """Combined authentication result."""
    requires_mfa: bool = False
    tokens: Optional[TokenResponse] = None
    mfa: Optional[MfaChallengeResponse] = None


class MfaSetupResponse(BaseModel):
    """Response schema for MFA setup information."""
    secret: str
    provisioning_uri: str
    recovery_codes: List[str]


class SocialAuthUrlResponse(BaseModel):
    """Response schema for social login URL."""
    url: str
