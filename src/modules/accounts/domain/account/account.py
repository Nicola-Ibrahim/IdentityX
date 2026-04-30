from datetime import datetime

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

    id: AccountId
    email: Email
    password: HashedPassword
    status: AccountStatus = Field(default_factory=AccountStatus.create)
    roles: set[AccountRole] = Field(default_factory=lambda: {AccountRole.USER}, repr=False)
    session_ids: list[SessionId] = Field(default_factory=list)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_verified(self) -> bool:
        return self.status.is_verified

    @property
    def is_active(self) -> bool:
        return self.status.is_active

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
            id=AccountId.create(),
            email=email,
            password=password,
            roles=roles or {AccountRole.USER},
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
            id=id,
            email=email,
            password=password,
            status=status,
            roles=roles,
            created_at=created_at,
            updated_at=updated_at,
            session_ids=session_ids or [],
        )

    def verify(self) -> None:
        if not self.status.is_verified:
            self.status = self.status.mark_verified()

    def deactivate(self) -> None:
        if self.status.is_active:
            self.status = self.status.deactivate()

    def activate(self) -> None:
        if not self.status.is_active:
            self.status = self.status.activate()

    def change_email(self, new_email: Email) -> None:
        if str(self.email) != str(new_email):
            self.email = new_email

    def change_password(self, new_hashed_password: HashedPassword) -> None:
        if self.password != new_hashed_password:
            self.password = new_hashed_password

    def assign_role(self, role: AccountRole) -> None:
        if role not in self.roles:
            self.roles.add(role)

    def remove_role(self, role: AccountRole) -> None:
        if role in self.roles:
            self.roles.remove(role)

    def can_login(self) -> bool:
        return self.status.is_active and self.status.is_verified
