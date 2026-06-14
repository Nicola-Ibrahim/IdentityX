from typing import override
from pydantic import BaseModel

from src.shared.building_blocks.application.events.base_event_bus import BaseEventBus
from src.shared.building_blocks.application.mediator import BaseCommand, BaseCommandHandler
from src.accounts.domain.session.repositories.session_repository import BaseSessionRepository
from src.accounts.domain.session.value_objects.refresh_token import RefreshToken
from src.accounts.domain.session.services.token_service import TokenService


class LogoutCommand(BaseModel, BaseCommand[None]):
    refresh_token: str


class LogoutHandler(BaseCommandHandler[LogoutCommand, None]):
    def __init__(
        self, token_service: TokenService, session_repo: BaseSessionRepository, event_bus: BaseEventBus
    ):
        self._token_service = token_service
        self._session_repo = session_repo
        self._event_bus = event_bus

    @override
    async def handle(self, command: LogoutCommand) -> None:
        try:
            refresh_vo = RefreshToken.create(command.refresh_token)
            self._token_service.validate_refresh_token(refresh_vo)
            session = await self._session_repo.get_by_refresh_token(refresh_vo)
            if session:
                session.revoke()
                await self._session_repo.update(session)
                await self._event_bus.publish_all(session.pull_events())
        except Exception:
            # Logout should be silent if token is already invalid
            pass
