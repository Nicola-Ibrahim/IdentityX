from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from typing import Self


class BaseUnitOfWork(ABC, AbstractAsyncContextManager["BaseUnitOfWork"]):
    """Abstract base class for the Unit of Work pattern.

    Provides a standard context manager implementation that delegates to
    begin/commit/rollback/close hooks.
    """

    async def __aenter__(self) -> Self:
        await self.begin()
        return self

    async def __aexit__(self, exc_type, exc_val, traceback) -> None:
        try:
            if exc_type is not None:
                await self.rollback()
        finally:
            await self.close()

    @abstractmethod
    async def begin(self) -> None:
        """Start a new transaction."""

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""

    @abstractmethod
    async def rollback(self) -> None:
        """Roll back the current transaction."""

    @abstractmethod
    async def close(self) -> None:
        """Close the underlying session/connection."""
