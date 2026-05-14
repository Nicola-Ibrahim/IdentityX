from __future__ import annotations
from typing import Any, Callable
from src.buckets.database.session import SQLAlchemySessionFactory, _current_session
from src.building_blocks.application.mediator import BaseCommand


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


class TransactionBehavior:
    """Mediator behavior for managing transactions."""

    def __init__(self, session_factory: SQLAlchemySessionFactory):
        self._session_factory = session_factory

    async def handle(self, request: Any, next_behavior: Callable[[], Any]) -> Any:
        if not isinstance(request, BaseCommand):
            return await next_behavior()

        async with TransactionScope(self._session_factory):
            return await next_behavior()
