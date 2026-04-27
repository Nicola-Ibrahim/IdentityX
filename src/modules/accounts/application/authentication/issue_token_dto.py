"""DTO returned after issuing an access token."""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class IssuedTokenDTO:
    access_token: str
    token_type: str = "bearer"
