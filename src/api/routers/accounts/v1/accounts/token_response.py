from pydantic import BaseModel
from src.modules.accounts.application.authentication.issue_token_pair_dto import IssuedTokenPairDTO


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

    @classmethod
    def from_dto(cls, dto: IssuedTokenPairDTO) -> "TokenResponse":
        return cls(
            access_token=dto.access_token,
            refresh_token=dto.refresh_token,
            token_type=dto.token_type,
            expires_in=dto.expires_in,
        )
