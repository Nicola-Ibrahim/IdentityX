import uuid

from pydantic import BaseModel

from ....building_blocks.application.mediator import BaseCommand, BaseCommandHandler
from ...domain.account.value_objects.account_id import AccountId
from ...domain.interfaces.account_repository import BaseAccountRepository
from ...domain.interfaces.session_repository import BaseSessionRepository
from ..dtos.account import AuthDTO


class SetActivationStatusCommand(BaseCommand[AuthDTO], BaseModel):
    account_id: str
    is_active: bool


class SetActivationStatusHandler(BaseCommandHandler[SetActivationStatusCommand, AuthDTO]):
    def __init__(self, account_repo: BaseAccountRepository, session_repo: BaseSessionRepository):
        self._account_repo = account_repo
        self._session_repo = session_repo

    async def handle(self, command: SetActivationStatusCommand) -> AuthDTO:
        try:
            account_id_vo = AccountId.create(uuid.UUID(command.account_id))
        except (ValueError, AttributeError) as exc:
            raise ValueError("Invalid account identifier") from exc

        account = await self._account_repo.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        if command.is_active:
            account.activate()
        else:
            account.deactivate()
            await self._session_repo.revoke_all_for_account(account.id)

        await self._account_repo.update(account)
        return AuthDTO.from_domain(account)
