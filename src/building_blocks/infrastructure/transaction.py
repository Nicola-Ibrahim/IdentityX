from __future__ import annotations
from src.buckets.database.session import SQLAlchemySessionFactory, _current_session

class TransactionScope:
    """Standalone async context manager for database transactions."""

    def __init__(self, session_factory: SQLAlchemySessionFactory) -> None:
        self._session_factory = session_factory

    async def __aenter__(self):
        self._session = self._session_factory()
        self._token = _current_session.set(self._session)
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                await self._session.rollback()
            else:
                await self._session.commit()
        finally:
            await self._session.close()
            _current_session.reset(self._token)
        return False
