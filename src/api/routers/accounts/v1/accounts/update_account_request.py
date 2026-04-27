"""Request schema for updating an account."""

from pydantic import BaseModel, EmailStr


class UpdateAccountRequest(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    is_active: bool | None = None
