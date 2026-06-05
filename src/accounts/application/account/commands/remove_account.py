from typing import override
import uuid

from pydantic import BaseModel

from src.building_blocks.application.mediator import BaseCommand, BaseCommandHandler
from src.accounts.domain.account.value_objects.account_id import AccountId
from src.accounts.domain.account.repositories.account_repository import BaseAccountRepository


class RemoveAccountCommand(BaseModel, BaseCommand[None]):
    account_id: str


class RemoveAccountHandler(BaseCommandHandler[RemoveAccountCommand, None]):
    def __init__(self, account_repo: BaseAccountRepository):
        self._account_repo = account_repo

    @override
    async def handle(self, command: RemoveAccountCommand) -> None:
        try:
            account_id_vo = AccountId.create(uuid.UUID(command.account_id))
        except (ValueError, AttributeError) as exc:
            raise ValueError("Invalid account identifier") from exc

        await self._account_repo.remove(account_id_vo)
