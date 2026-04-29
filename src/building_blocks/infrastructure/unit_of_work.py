from __future__ import annotations

from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Dict, Type, TypeVar

TRepository = TypeVar("TRepository")




class AsyncUnitOfWork(AbstractAsyncContextManager["AsyncUnitOfWork"]):
    """Base class for implementing the Asynchronous Unit of Work pattern."""

    def __init__(self) -> None:
        self._repositories: Dict[Type, object] = {}
        self._active = False

    # ------------------------------------------------------------------ #
    # Context manager API
    # ------------------------------------------------------------------ #
    async def __aenter__(self) -> "AsyncUnitOfWork":
        await self.begin()
        self._active = True
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type:
                await self.rollback()
            else:
                await self.commit()
        finally:
            self._active = False
            await self.close()

    # ------------------------------------------------------------------ #
    # Repository registry
    # ------------------------------------------------------------------ #
    def register_repository(self, repo_type: Type[TRepository], repo_instance: TRepository) -> None:
        self._repositories[repo_type] = repo_instance

    def get_repository(self, repo_type: Type[TRepository]) -> TRepository:
        repo = self._repositories.get(repo_type)
        if repo is None:
            raise KeyError(f"No repository registered for type: {repo_type!r}")
        return repo  # type: ignore[return-value]

    # ------------------------------------------------------------------ #
    # Hooks for subclasses
    # ------------------------------------------------------------------ #
    async def begin(self) -> None:
        """Hook for starting a transaction boundary."""

    async def commit(self) -> None:
        raise NotImplementedError

    async def rollback(self) -> None:
        raise NotImplementedError

    async def close(self) -> None:
        """Hook for cleaning up resources."""
