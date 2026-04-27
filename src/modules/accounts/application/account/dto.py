from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class AccountDTO:
    id: str
    email: str
    is_verified: bool
    is_active: bool
    roles: tuple[str, ...]
