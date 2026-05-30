from typing import override
import uuid
from pydantic import BaseModel
from src.building_blocks.application.mediator import BaseCommand, BaseCommandHandler
from src.accounts.domain.account.value_objects.account_id import AccountId
from src.accounts.domain.interfaces.session_repository import BaseSessionRepository


class RevokeAllSessionsCommand(BaseModel, BaseCommand[None]):
    account_id: str


class RevokeAllSessionsHandler(BaseCommandHandler[RevokeAllSessionsCommand, None]):
    def __init__(self, session_repo: BaseSessionRepository):
        self._session_repo = session_repo

    @override
    async def handle(self, command: RevokeAllSessionsCommand) -> None:
        try:
            account_id_vo = AccountId.create(uuid.UUID(command.account_id))
        except (ValueError, AttributeError) as exc:
            raise ValueError("Invalid account identifier") from exc

        await self._session_repo.revoke_all_for_account(account_id_vo)
