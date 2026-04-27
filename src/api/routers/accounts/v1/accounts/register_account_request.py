"""Request schema for registering a new account."""

from pydantic import BaseModel, EmailStr


class RegisterAccountRequest(BaseModel):
    email: EmailStr
    password: str
