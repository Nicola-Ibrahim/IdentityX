from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...domain.account.account import Account


@dataclass(slots=True, frozen=True)
class AccountDTO:
    id: str
    email: str
    is_verified: bool
    is_active: bool
    roles: tuple[str, ...]

    @classmethod
    def from_domain(cls, account: "Account") -> "AccountDTO":
        return cls(
            id=str(account.id.value),
            email=str(account.email),
            is_verified=account.is_verified,
            is_active=account.is_active,
            roles=tuple(r.value for r in account.roles),
        )
