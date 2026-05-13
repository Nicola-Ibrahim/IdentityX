from pydantic import BaseModel

from ....building_blocks.application.queries import BaseQuery
from ....building_blocks.application.mediator import BaseQuery,  Handler
from ....building_blocks.domain.result import Result
from ..interfaces.jwt import TokenService


class GetJwksQuery(BaseQuery[dict], BaseModel):
    pass


class GetJwksHandler(BaseQueryHandler[GetJwksQuery, dict]):
    def __init__(self, token_service: TokenService):
        self._token_service = token_service

    @Result.capture
    async def handle(self, query: GetJwksQuery) -> dict:
        return self._token_service.get_public_key_jwk()
