"""DTO returned by the register account handler."""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class RegisteredAccountDTO:
    id: str
    email: str
    is_verified: bool
    is_active: bool
