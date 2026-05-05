import uuid

from ....buckets.database.decorators import transactional
from ....building_blocks.domain.result import Result
from ...domain.account.account import Account
from ...domain.account.value_objects.account_id import AccountId
from ...domain.account.value_objects.email import Email
from ...domain.account.value_objects.hashed_password import HashedPassword
from ...domain.account.value_objects.password import Password
from ...domain.interfaces.uow import BaseAsyncUnitOfWork
from ..audit.service import AuditService
from ..interfaces.notification_service import BaseNotificationService
from ..interfaces.password_hasher import BasePasswordHasher
from .dto import AccountDTO


class AccountService:
    def __init__(
        self,
        uow: BaseAsyncUnitOfWork,
        password_hasher: BasePasswordHasher,
        notification_service: BaseNotificationService,
        audit_service: AuditService,
    ) -> None:
        self.uow = uow
        self._password_hasher = password_hasher
        self._notifications = notification_service
        self._audit = audit_service

    @Result.capture
    @transactional
    async def register(self, email: str, password: str) -> tuple[Account, AccountDTO]:
        email_vo = Email.create(email)
        password_vo = Password.create(password)

        hashed = HashedPassword.create(self._password_hasher.encode(password_vo.value))

        account = Account.register(email=email_vo, password=hashed)

        await self.uow.accounts.add(account)

        await self._notifications.send_welcome_email(str(email_vo))

        return AccountDTO.from_domain(account)

    @Result.capture
    @transactional
    async def get_by_id(self, account_id: str) -> AccountDTO:
        try:
            account_id_vo = AccountId.create(uuid.UUID(account_id))
        except (ValueError, AttributeError):
            return None

        account = await self.uow.accounts.get_by_id(account_id_vo)
        if not account:
            return None
        return AccountDTO.from_domain(account)

    @Result.capture
    @transactional
    async def list(self, limit: int = 100, offset: int = 0) -> tuple[tuple[AccountDTO, ...], int]:
        accounts_iter, total_count = await self.uow.accounts.list_accounts(limit=limit, offset=offset)
        accounts = [AccountDTO.from_domain(account) for account in accounts_iter]
        return tuple(accounts), total_count

    @Result.capture
    @transactional
    async def change_email(self, account_id: str, new_email: str) -> AccountDTO:
        account_id_vo = AccountId.create(uuid.UUID(account_id))

        account = await self.uow.accounts.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        account.change_email(Email.create(new_email))

        await self.uow.accounts.update(account)
        return AccountDTO.from_domain(account)

    @Result.capture
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
        return AccountDTO.from_domain(account)

    @Result.capture
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
        return AccountDTO.from_domain(account)

    @Result.capture
    @transactional
    async def remove(self, account_id: str) -> None:
        try:
            account_id_vo = AccountId.create(uuid.UUID(account_id))
        except (ValueError, AttributeError) as exc:
            raise ValueError("Invalid account identifier") from exc

        await self.uow.accounts.remove(account_id_vo)

    @Result.capture
    @transactional
    async def verify(self, account_id: str) -> tuple[Account, AccountDTO]:
        account_id_vo = AccountId.create(uuid.UUID(account_id))
        account = await self.uow.accounts.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        account.verify()
        await self.uow.accounts.update(account)
        return AccountDTO.from_domain(account)

    @Result.capture
    @transactional
    async def deactivate(self, account_id: str) -> AccountDTO:
        account_id_vo = AccountId.create(uuid.UUID(account_id))
        account = await self.uow.accounts.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        account.deactivate()
        await self.uow.accounts.update(account)
        return AccountDTO.from_domain(account)

    @Result.capture
    @transactional
    async def activate(self, account_id: str) -> AccountDTO:
        account_id_vo = AccountId.create(uuid.UUID(account_id))
        account = await self.uow.accounts.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        account.activate()
        await self.uow.accounts.update(account)
        return AccountDTO.from_domain(account)

    @Result.capture
    @transactional
    async def update(self, account_id: str, data: dict) -> AccountDTO:
        account_id_vo = AccountId.create(uuid.UUID(account_id))
        account = await self.uow.accounts.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        if "email" in data:
            account.change_email(Email.create(data["email"]))

        # Note: Generic update usually handles more fields, but for now we follow the existing pattern
        await self.uow.accounts.update(account)
        return AccountDTO.from_domain(account)
