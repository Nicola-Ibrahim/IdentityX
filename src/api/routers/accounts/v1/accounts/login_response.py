"""Response schema returned after successful login."""

from pydantic import BaseModel

from .account_response import AccountResponse


class LoginResponse(BaseModel):
    user: AccountResponse
    access_token: str
    refresh_token: str
    session_id: str
    token_type: str = "bearer"
