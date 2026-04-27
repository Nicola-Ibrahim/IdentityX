from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IssuedTokenPairDTO:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # access token TTL in seconds
