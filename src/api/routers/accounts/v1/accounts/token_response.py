from pydantic import BaseModel

from src.accounts.application.usecases.authentication.dtos.auth import TokenPair


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

    @classmethod
    def from_dto(cls, dto: TokenPair) -> "TokenResponse":
        return cls(
            access_token=dto.access_token,
            refresh_token=dto.refresh_token,
            token_type=dto.token_type,
            expires_in=dto.expires_in,
        )
