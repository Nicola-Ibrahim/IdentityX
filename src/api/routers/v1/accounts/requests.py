from pydantic import BaseModel, EmailStr


class RegisterAccountRequest(BaseModel):
    """Request schema for registering a new account."""

    email: EmailStr
    password: str
