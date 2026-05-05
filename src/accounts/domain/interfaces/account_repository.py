from abc import ABC, abstractmethod
from typing import Iterable, Optional

from ..account.account import Account
from ..account.value_objects.account_id import AccountId


class BaseAccountRepository(ABC):
    @abstractmethod
    async def add(self, account: Account) -> None:
        """Persist a newly created account aggregate."""

    @abstractmethod
    async def update(self, account: Account) -> None:
        """Persist modifications to an existing account."""

    @abstractmethod
    async def get_by_id(self, account_id: AccountId) -> Optional[Account]:
        """Retrieve an account by its identifier."""

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Account]:
        """Retrieve an account by email."""

    @abstractmethod
    async def get_by_external_identity(self, provider: str, provider_user_id: str) -> Optional[Account]:
        """Retrieve an account by an external provider identity (e.g. Google ID)."""

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Return ``True`` when an account already uses the email."""

    @abstractmethod
    async def list_accounts(self, limit: int = 100, offset: int = 0) -> tuple[Iterable[Account], int]:
        """Return accounts with pagination and total count, sorted by creation date."""

    @abstractmethod
    async def remove(self, account_id: AccountId) -> None:
        """Delete the account from persistence."""
