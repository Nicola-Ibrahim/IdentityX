from typing import override
from pydantic import BaseModel

from src.accounts.application.interfaces.jwt import TokenService
from src.building_blocks.application.mediator import BaseQuery, BaseQueryHandler


class GetJwksQuery(BaseModel, BaseQuery[dict]):
    pass


class GetJwksHandler(BaseQueryHandler[GetJwksQuery, dict]):
    def __init__(self, token_service: TokenService):
        self._token_service = token_service

    @override
    async def handle(self, query: GetJwksQuery) -> dict:
        return self._token_service.get_public_key_jwk()
