from pydantic import BaseModel, EmailStr
from typing import List, Optional


class RegisterAccountRequest(BaseModel):
    """Request schema for registering a new account."""
    email: EmailStr
    password: str


class UpdateAccountRequest(BaseModel):
    """Request schema for updating an account."""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class MfaSetupRequest(BaseModel):
    """Request schema for initiating MFA setup."""
    mfa_token: str


class MfaEnableRequest(BaseModel):
    """Request schema for enabling MFA."""
    mfa_token: str
    totp_code: str
    secret: str
    recovery_codes: List[str]


class MfaVerifyRequest(BaseModel):
    """Request schema for verifying MFA during login."""
    mfa_token: str
    totp_code: Optional[str] = None
    recovery_code: Optional[str] = None
    trust_device: bool = False
