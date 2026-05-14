import uuid
from typing import Any

from pydantic import BaseModel

from building_blocks.application.mediator import BaseCommand, BaseCommandHandler
from accounts.domain.account.value_objects.account_id import AccountId
from accounts.domain.account.value_objects.email import Email
from accounts.domain.interfaces.account_repository import BaseAccountRepository
from accounts.application.dtos.account import AccountDTO


class UpdateAccountCommand(BaseModel, BaseCommand[AccountDTO]):
    account_id: str
    data: dict[str, Any]


class UpdateAccountHandler(BaseCommandHandler[UpdateAccountCommand, AccountDTO]):
    def __init__(self, account_repo: BaseAccountRepository):
        self._account_repo = account_repo

    async def handle(self, command: UpdateAccountCommand) -> AccountDTO:
        try:
            account_id_vo = AccountId.create(uuid.UUID(command.account_id))
        except (ValueError, AttributeError) as exc:
            raise ValueError("Invalid account identifier") from exc

        account = await self._account_repo.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        if "email" in command.data:
            account.change_email(Email.create(command.data["email"]))

        await self._account_repo.update(account)
        return AccountDTO.from_domain(account)
