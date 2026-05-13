import uuid

from pydantic import BaseModel

from ....building_blocks.application.mediator import BaseCommand, BaseCommandHandler
from ...domain.account.value_objects.account_id import AccountId
from ...domain.interfaces.account_repository import BaseAccountRepository


class RemoveAccountCommand(BaseCommand[None], BaseModel):
    account_id: str


class RemoveAccountHandler(BaseCommandHandler[RemoveAccountCommand, None]):
    def __init__(self, account_repo: BaseAccountRepository):
        self._account_repo = account_repo

    async def handle(self, command: RemoveAccountCommand) -> None:
        try:
            account_id_vo = AccountId.create(uuid.UUID(command.account_id))
        except (ValueError, AttributeError) as exc:
            raise ValueError("Invalid account identifier") from exc

        await self._account_repo.remove(account_id_vo)
