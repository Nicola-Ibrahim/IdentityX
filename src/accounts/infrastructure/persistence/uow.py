from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.interfaces.uow import BaseAsyncUnitOfWork
from .repositories.sql_account_repo import SQLBaseAccountRepository
from .repositories.sql_audit_repo import SQLAuditLogRepository
from .repositories.sql_session_repo import SQLBaseSessionRepository


class SQLAlchemyUnitOfWork(BaseAsyncUnitOfWork):
    """SQLAlchemy implementation of the Unit of Work pattern."""

    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        self._session_factory = session_factory
        self._db_session: AsyncSession | None = None
        self._accounts: SQLBaseAccountRepository | None = None
        self._sessions: SQLBaseSessionRepository | None = None
        self._audit_logs: SQLAuditLogRepository | None = None

    async def begin(self) -> None:
        """Start a new session and initialize repositories."""
        self._db_session = self._session_factory()
        self._accounts = SQLBaseAccountRepository(self._db_session)
        self._sessions = SQLBaseSessionRepository(self._db_session)
        self._audit_logs = SQLAuditLogRepository(self._db_session)

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
            self._accounts = None
            self._sessions = None
            self._audit_logs = None

    @property
    def accounts(self) -> SQLBaseAccountRepository:
        if self._accounts is None:
            raise RuntimeError("Unit of Work not initialized. Call begin() or use as context manager.")
        return self._accounts

    @property
    def sessions(self) -> SQLBaseSessionRepository:
        if self._sessions is None:
            raise RuntimeError("Unit of Work not initialized. Call begin() or use as context manager.")
        return self._sessions

    @property
    def audit_logs(self) -> SQLAuditLogRepository:
        if self._audit_logs is None:
            raise RuntimeError("Unit of Work not initialized. Call begin() or use as context manager.")
        return self._audit_logs
