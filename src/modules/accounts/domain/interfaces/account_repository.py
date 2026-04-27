from abc import ABC, abstractmethod
from typing import Iterable, Optional

from ..account.account import Account
from ..account.value_objects.account_id import AccountId
from ..role.value_objects.role_id import RoleId


class AccountRepository(ABC):
    @abstractmethod
    def add(self, account: Account) -> None:
        """Persist a newly created account aggregate."""

    @abstractmethod
    def update(self, account: Account) -> None:
        """Persist modifications to an existing account."""

    @abstractmethod
    def get_by_id(self, account_id: AccountId) -> Optional[Account]:
        """Retrieve an account by its identifier."""

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[Account]:
        """Retrieve an account by email."""

    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """Return ``True`` when an account already uses the email."""

    @abstractmethod
    def list_accounts(self) -> Iterable[Account]:
        """Return all accounts sorted by creation date."""

    @abstractmethod
    def remove(self, account_id: AccountId) -> None:
        """Delete the account from persistence."""

    @abstractmethod
    def assign_role(self, account_id: AccountId, role_id: RoleId) -> None:
        """Associate a role with the account."""
