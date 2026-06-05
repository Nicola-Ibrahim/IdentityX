from typing import override
from pydantic import BaseModel

from src.building_blocks.application.events.base_event_bus import BaseEventBus
from src.accounts.application.account.dtos.account import AccountDTO
from src.accounts.application.interfaces.notification_service import BaseNotificationService
from src.accounts.domain.account.services.password_hasher import PasswordHasher
from src.accounts.domain.account.account import Account
from src.accounts.domain.account.value_objects.email import Email
from src.accounts.domain.account.value_objects.password import Password
from src.accounts.domain.account.repositories.account_repository import BaseAccountRepository
from src.building_blocks.application.mediator import BaseCommand, BaseCommandHandler


class RegisterAccountCommand(BaseModel, BaseCommand[AccountDTO]):
    email: str
    password: str


class RegisterAccountHandler(BaseCommandHandler[RegisterAccountCommand, AccountDTO]):
    def __init__(
        self,
        account_repo: BaseAccountRepository,
        notification_service: BaseNotificationService,
        password_hasher: PasswordHasher,
        event_bus: BaseEventBus,
    ):
        self._account_repo = account_repo
        self._notification_service = notification_service
        self._password_hasher = password_hasher
        self._event_bus = event_bus

    @override
    async def handle(self, command: RegisterAccountCommand) -> AccountDTO:
        email_vo = Email.create(command.email)
        password_vo = Password.create(command.password)
        hashed = self._password_hasher.encode(password_vo)
        account = Account.register(email=email_vo, password=hashed)
        await self._account_repo.add(account)
        await self._event_bus.publish_all(account.pull_events())
        await self._notification_service.send_welcome_email(str(email_vo))
        return AccountDTO(
            id=str(account.id.value),
            email=str(account.email),
            is_verified=account.is_verified,
            is_active=account.is_active,
            roles=tuple(r.value for r in account.roles),
        )
