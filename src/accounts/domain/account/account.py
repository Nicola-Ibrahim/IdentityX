from datetime import datetime, timedelta, timezone

from pydantic import Field

from ....building_blocks.domain.aggregate_root import AggregateRoot
from .enums.account_role import AccountRole
from .value_objects.account_id import AccountId
from .value_objects.email import Email
from .value_objects.external_identity import ExternalIdentity
from .value_objects.hashed_password import HashedPassword
from .value_objects.mfa_settings import MfaSettings
from .value_objects.session_id import SessionId
from .value_objects.status import Status
from .value_objects.trusted_device import TrustedDevice


class Account(AggregateRoot[AccountId]):
    """Aggregate root representing an account within the system."""

    id: AccountId
    email: Email
    password: HashedPassword | None = None
    status: Status = Field(default_factory=Status.create)
    roles: set[AccountRole] = Field(default_factory=lambda: {AccountRole.USER}, repr=False)
    session_ids: list[SessionId] = Field(default_factory=list)
    external_identities: list[ExternalIdentity] = Field(default_factory=list)
    mfa: MfaSettings = Field(default_factory=MfaSettings.create_disabled)
    trusted_devices: list[TrustedDevice] = Field(default_factory=list)

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def register(cls, email: Email, password: HashedPassword) -> "Account":
        """Register a new account with email/password."""
        return cls(id=AccountId.create(), email=email, password=password)

    @classmethod
    def from_data(
        cls,
        id: AccountId,
        email: Email,
        status: Status,
        roles: set[AccountRole],
        created_at: datetime,
        updated_at: datetime,
        password: HashedPassword | None = None,
        session_ids: list[SessionId] = Field(default_factory=list),
        external_identities: list[ExternalIdentity] = Field(default_factory=list),
        mfa: MfaSettings = Field(default_factory=MfaSettings.create_disabled),
        trusted_devices: list[TrustedDevice] = Field(default_factory=list),
    ) -> "Account":
        """Reconstruct an account from existing data (Repository use)."""
        account = cls(
            id=id,
            email=email,
            password=password,
            status=status,
            roles=roles,
            session_ids=session_ids,
            external_identities=external_identities,
            mfa=mfa,
            trusted_devices=trusted_devices,
        )
        # Ensure base metadata is set
        account.created_at = created_at
        account.updated_at = updated_at
        return account

    @classmethod
    def register_from_social(cls, email: Email, external_identity: ExternalIdentity) -> "Account":
        """Register a new account from social SSO."""
        account = cls(id=AccountId.create(), email=email)
        account.link_external_identity(external_identity)
        return account

    # ------------------------------------------------------------------
    # Domain Logic
    # ------------------------------------------------------------------

    def verify(self) -> None:
        self.status = self.status.verify()
        self.touch()

    def suspend(self) -> None:
        self.status = self.status.suspend()
        self.touch()

    def activate(self) -> None:
        self.status = self.status.activate()
        self.touch()

    def deactivate(self) -> None:
        self.status = self.status.deactivate()
        self.touch()

    def change_email(self, new_email: Email) -> None:
        self.email = new_email
        self.touch()

    def change_password(self, new_password: HashedPassword) -> None:
        self.password = new_password
        self.touch()

    def assign_role(self, role: AccountRole) -> None:
        self.roles.add(role)
        self.touch()

    def remove_role(self, role: AccountRole) -> None:
        if role in self.roles:
            self.roles.remove(role)
            self.touch()

    def link_external_identity(self, external_identity: ExternalIdentity) -> None:
        if any(i.provider == external_identity.provider for i in self.external_identities):
            return

        self.external_identities.append(external_identity)
        self.touch()

    def enable_mfa(self, secret: str, recovery_codes: list[str]) -> None:
        self.mfa = self.mfa.enable(secret, recovery_codes)
        self.touch()

    def disable_mfa(self) -> None:
        self.mfa = self.mfa.disable()
        self.touch()

    def consume_recovery_code(self, code: str) -> bool:
        success, new_mfa = self.mfa.verify_recovery_code(code)
        if success:
            self.mfa = new_mfa
            self.touch()
            return True
        return False

    def trust_device(self, device_hash: str, user_agent: str, ip_address: str, ttl_days: int = 30) -> None:
        # Remove existing
        self.trusted_devices = [d for d in self.trusted_devices if d.device_hash != device_hash]

        # Add new
        expires_at = datetime.now(timezone.utc) + timedelta(days=ttl_days)
        self.trusted_devices.append(
            TrustedDevice(device_hash=device_hash, user_agent=user_agent, ip_address=ip_address, expires_at=expires_at)
        )
        self.touch()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def can_login(self) -> bool:
        return self.status.is_active and self.status.is_verified

    def is_device_trusted(self, device_hash: str) -> bool:
        now = datetime.now(timezone.utc)
        return any(d.is_valid(device_hash, now) for d in self.trusted_devices)

    @property
    def is_verified(self) -> bool:
        return self.status.is_verified

    @property
    def is_active(self) -> bool:
        return self.status.is_active
