from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Dict, Type, TypeVar

TRepository = TypeVar("TRepository")


class UnitOfWork(AbstractContextManager["UnitOfWork"]):
    """Base class for implementing the Unit of Work pattern."""

    def __init__(self) -> None:
        self._repositories: Dict[Type, object] = {}
        self._active = False

    # ------------------------------------------------------------------ #
    # Context manager API
    # ------------------------------------------------------------------ #
    def __enter__(self) -> "UnitOfWork":
        self.begin()
        self._active = True
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type:
                self.rollback()
            else:
                self.commit()
        finally:
            self._active = False
            self.close()

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
    def begin(self) -> None:
        """Hook for starting a transaction boundary."""

    def commit(self) -> None:
        raise NotImplementedError

    def rollback(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        """Hook for cleaning up resources."""


class AbstractUnitOfWork(UnitOfWork):
    """Backwards compatible alias for the former abstract base class."""

    pass
