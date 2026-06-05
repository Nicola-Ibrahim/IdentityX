from pydantic import BaseModel


class MfaVerifyRequest(BaseModel):
    """Request schema for verifying MFA during login."""

    mfa_token: str
    totp_code: str | None = None
    recovery_code: str | None = None
    trust_device: bool = False
