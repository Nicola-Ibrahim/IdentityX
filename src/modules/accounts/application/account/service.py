import uuid
from .....database.decorators import transactional

from ...domain.account.account import Account
from ...domain.account.value_objects.account_id import AccountId
from ...domain.account.value_objects.email import Email
from ...domain.account.value_objects.hashed_password import HashedPassword
from ...domain.account.value_objects.password import Password
from ...domain.interfaces.unit_of_work import BaseUnitOfWork
from ..interfaces.notification_service import BaseNotificationService
from ..interfaces.password_hasher import BasePasswordHasher
from .dto import AccountDTO


class AccountService:
    def __init__(
        self,
        uow: BaseUnitOfWork,
        password_hasher: BasePasswordHasher,
        notification_service: BaseNotificationService,
    ) -> None:
        self.uow = uow
        self._password_hasher = password_hasher
        self._notifications = notification_service

    @transactional
    async def register(self, email: str, password: str) -> tuple[Account, AccountDTO]:
        email_vo = Email.create(email)
        password_vo = Password.create(password)

        hashed = HashedPassword.create(self._password_hasher.encode(password_vo.value))

        account = Account.register(email=email_vo, password=hashed)

        await self.uow.accounts.add(account)

        await self._notifications.send_welcome_email(str(email_vo))

        return account, self._to_dto(account)

    @transactional
    async def get_by_id(self, account_id: str) -> AccountDTO:
        try:
            account_id_vo = AccountId.create(uuid.UUID(account_id))
        except (ValueError, AttributeError):
            return None

        account = await self.uow.accounts.get_by_id(account_id_vo)
        if not account:
            return None
        return self._to_dto(account)

    @transactional
    async def list(self) -> tuple[AccountDTO, ...]:
        accounts_iter = await self.uow.accounts.list_accounts()
        accounts = [self._to_dto(account) for account in accounts_iter]
        return tuple(accounts)

    @transactional
    async def change_email(self, account_id: str, new_email: str) -> AccountDTO:
        account_id_vo = AccountId.create(uuid.UUID(account_id))

        account = await self.uow.accounts.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        account.change_email(Email.create(new_email))

        await self.uow.accounts.update(account)
        return self._to_dto(account)

    @transactional
    async def change_password(self, account_id: str, new_password: str) -> AccountDTO:
        account_id_vo = AccountId.create(uuid.UUID(account_id))

        account = await self.uow.accounts.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        hashed = HashedPassword.create(self._password_hasher.encode(new_password))
        account.change_password(hashed)

        # Security Side Effect: Revoke all sessions on password change
        await self.uow.sessions.revoke_all_for_account(account.id)

        await self.uow.accounts.update(account)
        return self._to_dto(account)

    @transactional
    async def set_activation_status(self, account_id: str, is_active: bool) -> AccountDTO:
        account_id_vo = AccountId.create(uuid.UUID(account_id))

        account = await self.uow.accounts.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        if is_active:
            account.activate()
        else:
            account.deactivate()
            # Security Side Effect: Revoke all sessions on deactivation
            await self.uow.sessions.revoke_all_for_account(account.id)

        await self.uow.accounts.update(account)
        return self._to_dto(account)

    def _to_dto(self, account: Account) -> AccountDTO:
        return AccountDTO(
            id=str(account.id.value),
            email=str(account.email),
            is_verified=account.is_verified,
            is_active=account.is_active,
            roles=tuple(r.value for r in account.roles),
        )

    @transactional
    async def remove(self, account_id: str) -> None:
        try:
            account_id_vo = AccountId.create(uuid.UUID(account_id))
        except (ValueError, AttributeError) as exc:
            raise ValueError("Invalid account identifier") from exc

        await self.uow.accounts.remove(account_id_vo)

    @transactional
    async def verify(self, account_id: str) -> tuple[Account, AccountDTO]:
        account_id_vo = AccountId.create(uuid.UUID(account_id))
        account = await self.uow.accounts.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        account.verify()
        await self.uow.accounts.update(account)
        return account, self._to_dto(account)
