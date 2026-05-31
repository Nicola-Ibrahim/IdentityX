from datetime import datetime, timedelta, timezone
from pydantic import Field

from src.building_blocks.domain.aggregate_root import AggregateRoot
from src.accounts.domain.account.enums.account_role import AccountRole
from src.accounts.domain.account.value_objects.account_id import AccountId
from src.accounts.domain.account.value_objects.email import Email
from src.accounts.domain.account.value_objects.external_identity import ExternalIdentity
from src.accounts.domain.account.value_objects.hashed_password import HashedPassword
from src.accounts.domain.account.value_objects.mfa_settings import MfaSettings
from src.accounts.domain.account.value_objects.session_id import SessionId
from src.accounts.domain.account.value_objects.status import Status
from src.accounts.domain.account.value_objects.trusted_device import TrustedDevice

from src.accounts.domain.account.rules.account_cannot_be_verified_twice_rule import AccountCannotBeVerifiedTwiceRule
from src.accounts.domain.account.rules.account_cannot_be_activated_if_already_active_rule import AccountCannotBeActivatedIfAlreadyActiveRule
from src.accounts.domain.account.rules.account_cannot_be_deactivated_if_already_inactive_rule import AccountCannotBeDeactivatedIfAlreadyInactiveRule

from src.accounts.domain.account.events.account_registered_event import AccountRegisteredEvent
from src.accounts.domain.account.events.account_verified_event import AccountVerifiedEvent
from src.accounts.domain.account.events.account_deactivated_event import AccountDeactivatedEvent
from src.accounts.domain.account.events.password_changed_event import PasswordChangedEvent
from src.accounts.domain.account.events.account_anonymized_event import AccountAnonymizedEvent
from src.accounts.domain.account.events.account_activated_event import AccountActivatedEvent
from src.accounts.domain.account.events.account_suspended_event import AccountSuspendedEvent
from src.accounts.domain.account.events.email_changed_event import EmailChangedEvent
from src.accounts.domain.account.events.mfa_enabled_event import MfaEnabledEvent
from src.accounts.domain.account.events.mfa_disabled_event import MfaDisabledEvent
from src.accounts.domain.account.events.device_trusted_event import DeviceTrustedEvent


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
        account = cls(id=AccountId.create(), email=email, password=password)
        account.record_event(
            AccountRegisteredEvent(
                account_id=str(account.id.value),
                email=str(account.email),
                roles=[r.value for r in account.roles],
            )
        )
        return account

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
        account.record_event(
            AccountRegisteredEvent(
                account_id=str(account.id.value),
                email=str(account.email),
                roles=[r.value for r in account.roles],
            )
        )
        return account

    # ------------------------------------------------------------------
    # Domain Logic
    # ------------------------------------------------------------------

    def verify(self) -> None:
        self.check_rules(AccountCannotBeVerifiedTwiceRule(is_verified=self.is_verified))
        self.status = self.status.verify()
        self.touch()
        self.record_event(AccountVerifiedEvent(account_id=str(self.id.value)))

    def suspend(self) -> None:
        self.check_rules(AccountCannotBeDeactivatedIfAlreadyInactiveRule(is_active=self.is_active))
        self.status = self.status.suspend()
        self.touch()
        self.record_event(AccountSuspendedEvent(account_id=str(self.id.value)))

    def activate(self) -> None:
        self.check_rules(AccountCannotBeActivatedIfAlreadyActiveRule(is_active=self.is_active))
        self.status = self.status.activate()
        self.touch()
        self.record_event(AccountActivatedEvent(account_id=str(self.id.value)))

    def deactivate(self) -> None:
        self.check_rules(AccountCannotBeDeactivatedIfAlreadyInactiveRule(is_active=self.is_active))
        self.status = self.status.deactivate()
        self.touch()
        self.record_event(AccountDeactivatedEvent(account_id=str(self.id.value)))

    def anonymize(self) -> None:
        """Scrubs PII for GDPR compliance and deactivates the account."""
        self.check_rules(AccountCannotBeDeactivatedIfAlreadyInactiveRule(is_active=self.is_active))
        # Scrub email and clear credentials/devices/mfa
        self.email = Email.create(f"anonymized_{self.id.value}@identityx.local")
        self.password = None
        self.external_identities = []
        self.mfa = MfaSettings.create_disabled()
        self.trusted_devices = []
        self.status = self.status.deactivate()
        self.touch()
        self.record_event(AccountAnonymizedEvent(account_id=str(self.id.value)))

    def change_email(self, new_email: Email) -> None:
        self.email = new_email
        self.touch()
        self.record_event(EmailChangedEvent(account_id=str(self.id.value), new_email=str(new_email)))

    def change_password(self, new_password: HashedPassword) -> None:
        self.password = new_password
        self.touch()
        self.record_event(PasswordChangedEvent(account_id=str(self.id.value)))

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
        self.record_event(MfaEnabledEvent(account_id=str(self.id.value)))

    def disable_mfa(self) -> None:
        self.mfa = self.mfa.disable()
        self.touch()
        self.record_event(MfaDisabledEvent(account_id=str(self.id.value)))

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
            TrustedDevice.create(device_hash=device_hash, user_agent=user_agent, ip_address=ip_address, expires_at=expires_at)
        )
        self.touch()
        self.record_event(DeviceTrustedEvent(account_id=str(self.id.value), device_hash=device_hash))

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
