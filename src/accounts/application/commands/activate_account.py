import uuid

from pydantic import BaseModel

from building_blocks.application.mediator import BaseCommand, BaseCommandHandler
from accounts.domain.account.value_objects.account_id import AccountId
from accounts.domain.interfaces.account_repository import BaseAccountRepository
from accounts.application.dtos.account import AccountDTO


class ActivateAccountCommand(BaseModel, BaseCommand[AccountDTO]):
    account_id: str


class ActivateAccountHandler(BaseCommandHandler[ActivateAccountCommand, AccountDTO]):
    def __init__(self, account_repo: BaseAccountRepository):
        self._account_repo = account_repo

    async def handle(self, command: ActivateAccountCommand) -> AccountDTO:
        try:
            account_id_vo = AccountId.create(uuid.UUID(command.account_id))
        except (ValueError, AttributeError) as exc:
            raise ValueError("Invalid account identifier") from exc

        account = await self._account_repo.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        account.activate()
        await self._account_repo.update(account)
        return AccountDTO.from_domain(account)
