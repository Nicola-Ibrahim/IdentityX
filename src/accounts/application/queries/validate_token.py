from typing import override
from pydantic import BaseModel

from accounts.application.interfaces.jwt import TokenService
from accounts.domain.interfaces.session_repository import BaseSessionRepository
from accounts.domain.session.token_errors import TokenRevokedException
from accounts.domain.session.value_objects.session_id import SessionId
from building_blocks.application.mediator import BaseQuery, BaseQueryHandler


class ValidateTokenQuery(BaseModel, BaseQuery[str]):
    token: str


class ValidateTokenHandler(BaseQueryHandler[ValidateTokenQuery, str]):
    def __init__(self, token_service: TokenService, session_repo: BaseSessionRepository):
        self._token_service = token_service
        self._session_repo = session_repo

    @override
    async def handle(self, query: ValidateTokenQuery) -> str:
        # 1. Cryptographic Check (JWT Signature & Expiration)
        claims = self._token_service.validate_access_token(query.token)

        # 2. Stateful Check (Revocation)
        # Access tokens should have an 'sid' (Session ID) claim linked to the database session.
        if claims.sid:
            session_id = SessionId(claims.sid)
            session = await self._session_repo.get_by_id(session_id)

            # If the session doesn't exist or is marked as revoked, block access immediately.
            if not session or session.is_revoked:
                raise TokenRevokedException("Session has been revoked")

        return claims.sub
