from typing import Iterable

from pydantic import Field

from .....building_blocks.domain.aggregate_root import AggregateRoot
from .value_objects.account_id import AccountId
from .value_objects.account_role import AccountRole
from .value_objects.account_status import AccountStatus
from .value_objects.email import Email
from .value_objects.hashed_password import HashedPassword


class Account(AggregateRoot[AccountId]):
    """Aggregate root representing an account within the system."""

    _id: AccountId
    _email: Email
    _password: HashedPassword
    _status: AccountStatus = Field(default_factory=AccountStatus.create)
    _roles: set[AccountRole] = Field(default_factory=lambda: {AccountRole.USER}, repr=False)

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

    # ------------------------------------------------------------------
    # Behaviour
    # ------------------------------------------------------------------
    @classmethod
    def register(cls, email: Email, hashed_password: HashedPassword) -> "Account":
        account = cls(_id=AccountId.create(), _email=email, _password=hashed_password)
        return account

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
