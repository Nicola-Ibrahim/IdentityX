from pydantic import BaseModel

from ....building_blocks.application.mediator import BaseCommand, BaseCommandHandler
from ...domain.interfaces.session_repository import BaseSessionRepository
from ...domain.session.value_objects.refresh_token import RefreshToken
from ..interfaces.jwt import TokenService


class LogoutCommand(BaseCommand[None], BaseModel):
    refresh_token: str


class LogoutHandler(BaseCommandHandler[LogoutCommand, None]):
    def __init__(self, token_service: TokenService, session_repo: BaseSessionRepository):
        self._token_service = token_service
        self._session_repo = session_repo

    async def handle(self, command: LogoutCommand) -> None:
        try:
            self._token_service.validate_refresh_token(command.refresh_token)
            session = await self._session_repo.get_by_refresh_token(RefreshToken.create(command.refresh_token))
            if session:
                session.revoke()
                await self._session_repo.update(session)
        except Exception:
            # Logout should be silent if token is already invalid
            pass
