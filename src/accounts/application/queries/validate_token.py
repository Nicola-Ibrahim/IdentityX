from pydantic import BaseModel

from building_blocks.application.mediator import BaseQuery, BaseQueryHandler
from building_blocks.domain.result import Result
from accounts.application.interfaces.jwt import TokenService


class ValidateTokenQuery(BaseModel, BaseQuery[str]):
    token: str


class ValidateTokenHandler(BaseQueryHandler[ValidateTokenQuery, str]):
    def __init__(self, token_service: TokenService):
        self._token_service = token_service

    @Result.capture
    async def handle(self, query: ValidateTokenQuery) -> str:
        claims = self._token_service.validate_access_token(query.token)
        return claims.sub
