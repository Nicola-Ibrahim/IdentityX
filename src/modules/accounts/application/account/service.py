import uuid
from typing import Any

from ...domain.account.account import Account
from ...domain.account.value_objects.account_id import AccountId
from ...domain.account.value_objects.email import Email
from ...domain.account.value_objects.hashed_password import HashedPassword
from ...domain.account.value_objects.password import Password
from ...domain.interfaces.unit_of_work import UnitOfWork
from ..interfaces.notification_service import INotificationService
from ..interfaces.password_hasher import IPasswordHasher
from .dto import AccountDTO


class AccountService:
    def __init__(
        self,
        uow: UnitOfWork,
        password_hasher: IPasswordHasher,
        notification_service: INotificationService,
    ) -> None:
        self.uow = uow
        self._password_hasher = password_hasher
        self._notifications = notification_service

    def register(self, email: str, password: str) -> tuple[Account, AccountDTO]:
        with self.uow:
            email_vo = Email.create(email)
            password_vo = Password.create(password)

            if self.uow.accounts.exists_by_email(str(email_vo)):
                raise ValueError("An account with this email already exists")

            hashed = HashedPassword.create(self._password_hasher.encode(password_vo.value))

            account = Account.register(email=email_vo, hashed_password=hashed)

            self.uow.accounts.add(account)
            self.uow.commit()

            self._notifications.send_welcome_email(str(email_vo))

            dto = AccountDTO(
                id=str(account.id.value),
                email=str(email_vo),
                is_verified=account.is_verified,
                is_active=account.is_active,
            )
            return account, dto

    def get_by_id(self, account_id: str) -> AccountDTO:
        try:
            account_id = AccountId.create(uuid.UUID(account_id))
        except (ValueError, AttributeError):
            return None
        with self.uow:
            account = self.uow.accounts.get_by_id(account_id)
            if not account:
                return None
            return AccountDTO(
                id=str(account.id.value),
                email=str(account.email),
                is_verified=account.is_verified,
                is_active=account.is_active,
                roles=tuple(r.value for r in account.roles),
            )

    def list(self) -> tuple[AccountDTO, ...]:
        with self.uow:
            accounts = (
                AccountDTO(
                    id=str(account.id.value),
                    email=str(account.email),
                    is_verified=account.is_verified,
                    is_active=account.is_active,
                    roles=tuple(r.value for r in account.roles),
                )
                for account in self.uow.accounts.list_accounts()
            )
            return tuple(accounts)

    def update(self, account_id: str, data: dict[str, Any]) -> AccountDTO:
        account_id = AccountId.create(uuid.UUID(account_id))

        with self.uow:
            account = self.uow.accounts.get_by_id(account_id)
            if not account:
                raise ValueError("Account not found")

            if data.get("email"):
                account.change_email(Email.create(data["email"]))
            if data.get("password"):
                hashed = HashedPassword.create(self._password_hasher.encode(data["password"]))
                account.change_password(hashed)
            if data.get("is_active") is True:
                account.activate()
            elif data.get("is_active") is False:
                account.deactivate()

            self.uow.accounts.update(account)
            self.uow.commit()

            dto = AccountDTO(
                id=str(account.id.value),
                email=str(account.email),
                is_verified=account.is_verified,
                is_active=account.is_active,
                roles=tuple(r.value for r in account.roles),
            )
            return dto

    def remove(self, account_id: str) -> None:
        try:
            account_id = AccountId.create(uuid.UUID(account_id))
        except (ValueError, AttributeError) as exc:
            raise ValueError("Invalid account identifier") from exc
        with self.uow:
            self.uow.accounts.remove(account_id)
            self.uow.commit()

    def verify(self, account_id: str) -> tuple[Account, AccountDTO]:
        account_id = AccountId.create(uuid.UUID(account_id))
        with self.uow:
            account = self.uow.accounts.get_by_id(account_id)
            if not account:
                raise ValueError("Account not found")

            account.verify()
            self.uow.accounts.update(account)
            self.uow.commit()

            dto = AccountDTO(
                id=str(account.id.value),
                email=str(account.email),
                is_verified=account.is_verified,
                is_active=account.is_active,
                roles=tuple(r.value for r in account.roles),
            )
            return account, dto
