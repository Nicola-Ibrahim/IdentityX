from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.interfaces.unit_of_work import BaseUnitOfWork
from .repositories.sql_account_repo import SQLBaseAccountRepository
from .repositories.sql_session_repo import SQLBaseSessionRepository


class SQLAlchemyUnitOfWork(BaseUnitOfWork):
    """SQLAlchemy implementation of the Unit of Work pattern."""

    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        self._session_factory = session_factory
        self._db_session: AsyncSession | None = None

    async def begin(self) -> None:
        """Start a new session and initialize repositories."""
        self._db_session = self._session_factory()
        self.accounts = SQLBaseAccountRepository(self._db_session)
        self.sessions = SQLBaseSessionRepository(self._db_session)

    async def commit(self) -> None:
        """Commit the current transaction."""
        if self._db_session:
            await self._db_session.commit()

    async def rollback(self) -> None:
        """Roll back the current transaction."""
        if self._db_session:
            await self._db_session.rollback()

    async def close(self) -> None:
        """Close the underlying session."""
        if self._db_session:
            await self._db_session.close()
            self._db_session = None
