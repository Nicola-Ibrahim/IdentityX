from typing import Callable, Self

from sqlalchemy.orm import Session

from ...domain.interfaces.unit_of_work import UnitOfWork
from .repositories.sql_account_repo import SQLAccountRepository
from .repositories.sql_session_repo import SQLSessionRepository


class SQLAlchemyUnitOfWork(UnitOfWork):
    """SQLAlchemy implementation of the Unit of Work pattern."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None

    def __enter__(self) -> Self:
        self._session = self._session_factory()
        self.accounts = SQLAccountRepository(self._session)
        self.sessions = SQLSessionRepository(self._session)
        return self

    def __exit__(self, exc_type, exc_val, traceback) -> None:
        if self._session:
            if exc_type:
                self.rollback()
            self._session.close()
        self._session = None

    def commit(self) -> None:
        if self._session:
            self._session.commit()

    def rollback(self) -> None:
        if self._session:
            self._session.rollback()
