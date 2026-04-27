"""Request schema for verifying an account."""

from pydantic import BaseModel


class VerifyAccountRequest(BaseModel):
    user_id: str

    @property
    def account_id(self) -> str:
        return self.user_id
