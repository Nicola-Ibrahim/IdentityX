from pydantic import BaseModel, EmailStr


class UpdateAccountRequest(BaseModel):
    """Request schema for updating an account."""

    email: EmailStr | None = None
    password: str | None = None
    is_active: bool | None = None


class MfaSetupRequest(BaseModel):
    """Request schema for initiating MFA setup."""

    mfa_token: str


class MfaEnableRequest(BaseModel):
    """Request schema for enabling MFA."""

    mfa_token: str
    totp_code: str
    secret: str
    recovery_codes: list[str]
