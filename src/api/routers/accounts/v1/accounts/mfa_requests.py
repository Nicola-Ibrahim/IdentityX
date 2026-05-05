from pydantic import BaseModel


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
