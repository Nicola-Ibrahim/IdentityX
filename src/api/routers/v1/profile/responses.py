from pydantic import BaseModel


class MfaSetupResponse(BaseModel):
    """Response schema for MFA setup information."""

    secret: str
    provisioning_uri: str
    recovery_codes: list[str]
