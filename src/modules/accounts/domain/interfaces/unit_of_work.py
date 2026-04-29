from abc import ABC, abstractmethod
from typing import Self

from .account_repository import AccountRepository
from .session_repository import SessionRepository


class UnitOfWork(ABC):
    """Abstract base class for the Unit of Work pattern.

    This interface defines the transaction boundary and provides access to repositories.
    """

    accounts: AccountRepository
    sessions: SessionRepository

    @abstractmethod
    async def __aenter__(self) -> Self: ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, traceback) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
