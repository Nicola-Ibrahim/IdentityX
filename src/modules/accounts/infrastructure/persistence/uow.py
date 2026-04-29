from typing import Callable, Self

from sqlalchemy.ext.asyncio import AsyncSession

from ....building_blocks.infrastructure.unit_of_work import AsyncUnitOfWork
from ...domain.interfaces.unit_of_work import UnitOfWork as IUnitOfWork
from .repositories.sql_account_repo import SQLAccountRepository
from .repositories.sql_session_repo import SQLSessionRepository


class SQLAlchemyUnitOfWork(AsyncUnitOfWork, IUnitOfWork):
    """SQLAlchemy implementation of the Unit of Work pattern."""

    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        super().__init__()
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self.accounts = SQLAccountRepository(self._session)
        self.sessions = SQLSessionRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, traceback) -> None:
        try:
            await super().__aexit__(exc_type, exc_val, traceback)
        finally:
            if self._session:
                await self._session.close()
            self._session = None

    async def commit(self) -> None:
        if self._session:
            await self._session.commit()

    async def rollback(self) -> None:
        if self._session:
            await self._session.rollback()
