from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class UpdateRequest(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    is_active: bool | None = None


class MfaSetupRequest(BaseModel):
    mfa_token: str


class MfaEnableRequest(BaseModel):
    mfa_token: str
    totp_code: str
    secret: str
    recovery_codes: list[str]


class MfaVerifyRequest(BaseModel):
    mfa_token: str
    totp_code: str | None = None
    recovery_code: str | None = None
    trust_device: bool = False
