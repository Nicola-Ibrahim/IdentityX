from typing import override
import uuid

from pydantic import BaseModel

from src.shared.building_blocks.application.events.base_event_bus import BaseEventBus
from src.shared.building_blocks.application.mediator import BaseCommand, BaseCommandHandler
from src.accounts.domain.account.value_objects.account_id import AccountId
from src.accounts.domain.account.repositories.account_repository import BaseAccountRepository
from src.accounts.application.account.dtos.account import AccountDTO


class DeactivateAccountCommand(BaseModel, BaseCommand[AccountDTO]):
    account_id: str


class DeactivateAccountHandler(BaseCommandHandler[DeactivateAccountCommand, AccountDTO]):
    def __init__(self, account_repo: BaseAccountRepository, event_bus: BaseEventBus):
        self._account_repo = account_repo
        self._event_bus = event_bus

    @override
    async def handle(self, command: DeactivateAccountCommand) -> AccountDTO:
        try:
            account_id_vo = AccountId.create(uuid.UUID(command.account_id))
        except (ValueError, AttributeError) as exc:
            raise ValueError("Invalid account identifier") from exc

        account = await self._account_repo.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        account.deactivate()
        await self._account_repo.update(account)
        await self._event_bus.publish_all(account.pull_events())
        return AccountDTO(
            id=str(account.id.value),
            email=str(account.email),
            is_verified=account.is_verified,
            is_active=account.is_active,
            roles=tuple(r.value for r in account.roles),
        )
