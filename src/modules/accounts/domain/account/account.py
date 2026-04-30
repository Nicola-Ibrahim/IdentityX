from datetime import datetime, timezone
from typing import Iterable

from pydantic import Field

from .....building_blocks.domain.aggregate_root import AggregateRoot
from .value_objects.account_id import AccountId
from .value_objects.account_role import AccountRole
from .value_objects.account_status import AccountStatus
from .value_objects.email import Email
from .value_objects.hashed_password import HashedPassword
from .value_objects.session_id import SessionId


class Account(AggregateRoot[AccountId]):
    """Aggregate root representing an account within the system."""

    _id: AccountId
    _email: Email
    _password: HashedPassword
    _status: AccountStatus = Field(default_factory=AccountStatus.create)
    _roles: set[AccountRole] = Field(default_factory=lambda: {AccountRole.USER}, repr=False)
    _session_ids: list[SessionId] = Field(default_factory=list)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def email(self) -> Email:
        return self._email

    @property
    def hashed_password(self) -> HashedPassword:
        return self._password

    @property
    def is_verified(self) -> bool:
        return self._status.is_verified

    @property
    def is_active(self) -> bool:
        return self._status.is_active

    @property
    def roles(self) -> Iterable[AccountRole]:
        return tuple(self._roles)

    @property
    def session_ids(self) -> Iterable[SessionId]:
        return tuple(self._session_ids)

    # ------------------------------------------------------------------
    # Behaviour
    # ------------------------------------------------------------------
    @classmethod
    def register(
        cls,
        email: Email,
        password: HashedPassword,
        roles: set[AccountRole] | None = None,
    ) -> "Account":
        """Factory method to register a new account aggregate."""
        return cls(
            _id=AccountId.create(),
            _email=email,
            _password=password,
            _roles=roles or {AccountRole.USER},
            _created_at=datetime.now(timezone.utc),
            _updated_at=datetime.now(timezone.utc),
        )

    @classmethod
    def from_data(
        cls,
        id: AccountId,
        email: Email,
        password: HashedPassword,
        status: AccountStatus,
        roles: set[AccountRole],
        created_at: datetime,
        updated_at: datetime,
        session_ids: list[SessionId] | None = None,
    ) -> "Account":
        """Reconstitute an account from existing data (e.g. from persistence)."""
        return cls(
            _id=id,
            _email=email,
            _password=password,
            _status=status,
            _roles=roles,
            _created_at=created_at,
            _updated_at=updated_at,
            _session_ids=session_ids or [],
        )

    def verify(self) -> None:
        if not self._status.is_verified:
            self._status = self._status.mark_verified()

    def deactivate(self) -> None:
        if self._status.is_active:
            self._status = self._status.deactivate()

    def activate(self) -> None:
        if not self._status.is_active:
            self._status = self._status.activate()

    def change_email(self, new_email: Email) -> None:
        if str(self._email) != str(new_email):
            self._email = new_email

    def change_password(self, new_hashed_password: HashedPassword) -> None:
        if self._password != new_hashed_password:
            self._password = new_hashed_password

    def assign_role(self, role: AccountRole) -> None:
        if role not in self._roles:
            self._roles.add(role)

    def remove_role(self, role: AccountRole) -> None:
        if role in self._roles:
            self._roles.remove(role)

    def can_login(self) -> bool:
        return self._status.is_active and self._status.is_verified
