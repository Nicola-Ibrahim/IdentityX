from pydantic import BaseModel


class AccountResponse(BaseModel):
    id: str
    email: str
    is_verified: bool
    is_active: bool
    roles: list[str] = []
