from pydantic import BaseModel

from building_blocks.application.mediator import BaseQuery, BaseQueryHandler
from building_blocks.domain.result import Result
from accounts.application.interfaces.jwt import TokenService


class GetJwksQuery(BaseModel, BaseQuery[dict]):
    pass


class GetJwksHandler(BaseQueryHandler[GetJwksQuery, dict]):
    def __init__(self, token_service: TokenService):
        self._token_service = token_service

    @Result.capture
    async def handle(self, query: GetJwksQuery) -> dict:
        return self._token_service.get_public_key_jwk()
