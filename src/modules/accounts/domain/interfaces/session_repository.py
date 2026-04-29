"""Repository interface for session aggregates."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from ..account.value_objects.account_id import AccountId
from ..session.session import Session
from ..session.value_objects.refresh_token import RefreshToken
from ..session.value_objects.session_id import SessionId


class BaseSessionRepository(ABC):
    @abstractmethod
    async def add(self, session: Session) -> None:
        """Persist a newly issued session."""

    @abstractmethod
    async def update(self, session: Session) -> None:
        """Persist changes to an existing session."""

    @abstractmethod
    async def get_by_id(self, session_id: SessionId) -> Optional[Session]:
        """Return a session by its identifier."""

    @abstractmethod
    async def get_by_refresh_token(self, token: RefreshToken) -> Optional[Session]:
        """Return a session by its refresh token value."""

    @abstractmethod
    async def list_for_account(self, account_id: AccountId) -> Iterable[Session]:
        """Return all sessions owned by the account."""

    @abstractmethod
    async def revoke_all_for_account(self, account_id: AccountId) -> None:
        """Revoke all active sessions for the account."""
