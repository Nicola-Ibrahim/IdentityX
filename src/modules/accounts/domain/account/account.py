from typing import Iterable

from pydantic import Field

from .....building_blocks.domain.aggregate_root import AggregateRoot
from ..role.value_objects.role_id import RoleId
from .value_objects.account_id import AccountId
from .value_objects.account_status import AccountStatus
from .value_objects.email import Email
from .value_objects.hashed_password import HashedPassword


class Account(AggregateRoot[AccountId]):
    """Aggregate root representing an account within the system."""

    _id: AccountId
    _email: Email
    _password: HashedPassword
    _status: AccountStatus = Field(default_factory=AccountStatus.create)
    _role_ids: set[RoleId] = Field(default_factory=set, repr=False)

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
    def role_ids(self) -> Iterable[RoleId]:
        return tuple(self._role_ids)

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

    def assign_role(self, role_id: RoleId) -> None:
        if role_id not in self._role_ids:
            self._role_ids.add(role_id)

    def remove_role(self, role_id: RoleId) -> None:
        if role_id in self._role_ids:
            self._role_ids.remove(role_id)

    def can_login(self) -> bool:
        return self._status.is_active and self._status.is_verified
