from pydantic import BaseModel


class AccountDTO(BaseModel):
    id: str
    email: str
    is_verified: bool
    is_active: bool
    roles: tuple[str, ...]
