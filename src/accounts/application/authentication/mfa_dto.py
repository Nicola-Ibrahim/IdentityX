from pydantic import BaseModel


class MfaSetupDTO(BaseModel):
    """Data returned when initiating MFA setup."""

    secret: str
    provisioning_uri: str  # otpauth:// URI for QR codes
    recovery_codes: list[str]


class MfaChallengeDTO(BaseModel):
    """Data returned when MFA is required during login."""

    mfa_token: str  # Short-lived JWT (typ="mfa")
    mfa_setup_required: bool
