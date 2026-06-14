from src.accounts.domain.account.account import Account
from src.accounts.domain.account.enums.account_role import AccountRole
from src.accounts.domain.account.value_objects.account_id import AccountId
from src.accounts.domain.account.value_objects.email import Email
from src.accounts.domain.account.value_objects.external_identity import ExternalIdentity
from src.accounts.domain.account.value_objects.hashed_password import HashedPassword
from src.accounts.domain.account.value_objects.mfa_settings import MfaSettings
from src.accounts.domain.account.value_objects.session_id import SessionId
from src.accounts.domain.account.value_objects.status import Status
from src.accounts.domain.account.value_objects.trusted_device import TrustedDevice
from src.accounts.infrastructure.persistence.tables import AccountTable, ExternalIdentityTable, TrustedDeviceTable


class AccountMapper:
    @staticmethod
    def to_domain(record: AccountTable) -> Account:
        roles = {AccountRole(r.strip()) for r in record.roles.split(",") if r.strip()}

        # Extract session IDs if available
        session_ids = []
        try:
            session_ids = [SessionId.create(s.id) for s in record.sessions]
        except Exception:
            pass

        return Account.from_data(
            id=AccountId.create(record.id),
            email=Email.create(record.email),
            password=HashedPassword.create(record.hashed_password) if record.hashed_password else None,
            status=Status(is_verified=record.is_verified, is_active=record.is_active),
            roles=roles,
            session_ids=session_ids,
            created_at=record.created_at,
            updated_at=record.updated_at,
            external_identities=[
                ExternalIdentity.create(i.provider, i.provider_user_id) for i in record.external_identities
            ],
            mfa=MfaSettings(
                enabled=record.mfa_enabled,
                secret=record.mfa_secret,
                recovery_codes=record.mfa_recovery_codes.split(",") if record.mfa_recovery_codes else [],
            ),
            trusted_devices=[
                TrustedDevice(
                    device_hash=d.device_hash,
                    user_agent=d.user_agent,
                    ip_address=d.ip_address,
                    expires_at=d.expires_at,
                    created_at=d.created_at,
                )
                for d in record.trusted_devices
            ],
        )

    @staticmethod
    def to_record(account: Account) -> AccountTable:
        return AccountTable(
            id=account.id.value,
            email=str(account.email),
            hashed_password=account.password.value if account.password else None,
            is_verified=account.status.is_verified,
            is_active=account.status.is_active,
            roles=",".join(r.value for r in account.roles),
            external_identities=[
                ExternalIdentityTable(provider=i.provider, provider_user_id=i.provider_user_id)
                for i in account.external_identities
            ],
            mfa_enabled=account.mfa.enabled,
            mfa_secret=account.mfa.secret,
            mfa_recovery_codes=",".join(account.mfa.recovery_codes) if account.mfa.recovery_codes else None,
            trusted_devices=[
                TrustedDeviceTable(
                    device_hash=d.device_hash,
                    user_agent=d.user_agent,
                    ip_address=d.ip_address,
                    expires_at=d.expires_at,
                    created_at=d.created_at,
                )
                for d in account.trusted_devices
            ],
        )

    @staticmethod
    def update_record(account: Account, record: AccountTable) -> None:
        record.email = str(account.email)
        record.hashed_password = account.password.value if account.password else None
        record.is_active = account.status.is_active
        record.is_verified = account.status.is_verified
        record.roles = ",".join(r.value for r in account.roles)

        # Update external identities (sync)
        record.external_identities = [
            ExternalIdentityTable(provider=i.provider, provider_user_id=i.provider_user_id)
            for i in account.external_identities
        ]
        record.mfa_enabled = account.mfa.enabled
        record.mfa_secret = account.mfa.secret
        record.mfa_recovery_codes = ",".join(account.mfa.recovery_codes) if account.mfa.recovery_codes else None

        # Update trusted devices (sync)
        record.trusted_devices = [
            TrustedDeviceTable(
                account_id=account.id.value,
                device_hash=d.device_hash,
                user_agent=d.user_agent,
                ip_address=d.ip_address,
                expires_at=d.expires_at,
                created_at=d.created_at,
            )
            for d in account.trusted_devices
        ]
