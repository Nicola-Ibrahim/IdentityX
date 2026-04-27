"""DTO returned after successful authentication."""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class LoginResultDTO:
    account_id: str
    email: str
    session_id: str
    refresh_token: str
