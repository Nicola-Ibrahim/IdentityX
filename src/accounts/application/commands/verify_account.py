import uuid

from pydantic import BaseModel

from ....building_blocks.application.mediator import BaseCommand, BaseCommandHandler
from ...domain.account.value_objects.account_id import AccountId
from ...domain.interfaces.account_repository import BaseAccountRepository
from ..dtos.account import AuthDTO


class VerifyAccountCommand(BaseCommand[AuthDTO], BaseModel):
    account_id: str


class VerifyAccountHandler(BaseCommandHandler[VerifyAccountCommand, AuthDTO]):
    def __init__(self, account_repo: BaseAccountRepository):
        self._account_repo = account_repo

    async def handle(self, command: VerifyAccountCommand) -> AuthDTO:
        try:
            account_id_vo = AccountId.create(uuid.UUID(command.account_id))
        except (ValueError, AttributeError) as exc:
            raise ValueError("Invalid account identifier") from exc

        account = await self._account_repo.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        account.verify()
        await self._account_repo.update(account)
        return AuthDTO.from_domain(account)
