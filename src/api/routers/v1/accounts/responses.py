from pydantic import BaseModel


class AccountResponse(BaseModel):
    """Public representation of an account."""

    id: str
    email: str
    is_verified: bool
    is_active: bool
    roles: list[str]
