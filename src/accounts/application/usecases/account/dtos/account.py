from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from ...domain.account.account import Account


class AuthDTO(BaseModel):
    id: str
    email: str
    is_verified: bool
    is_active: bool
    roles: tuple[str, ...]

    @classmethod
    def from_domain(cls, account: "Account") -> "AuthDTO":
        return cls(
            id=str(account.id.value),
            email=str(account.email),
            is_verified=account.is_verified,
            is_active=account.is_active,
            roles=tuple(r.value for r in account.roles),
        )
