from pydantic import BaseModel, EmailStr

from ......modules.accounts.domain.account import Account


class AccountResponse(BaseModel):
    id: str
    email: EmailStr
    is_verified: bool
    is_active: bool

    @classmethod
    def from_domain(cls, account: Account) -> "AccountResponse":
        return cls(
            id=str(account.id.value),
            email=str(account.email),
            is_verified=account.is_verified,
            is_active=account.is_active,
        )
