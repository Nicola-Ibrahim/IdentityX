from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from .....buckets.database.repository import SQLBaseRepository
from ....domain.account.account import Account
from ....domain.account.enums.account_role import AccountRole
from ....domain.account.value_objects.account_id import AccountId
from ....domain.account.value_objects.email import Email
from ....domain.account.value_objects.external_identity import ExternalIdentity
from ....domain.account.value_objects.hashed_password import HashedPassword
from ....domain.account.value_objects.mfa_settings import MfaSettings
from ....domain.account.value_objects.session_id import SessionId
from ....domain.account.value_objects.status import Status
from ....domain.account.value_objects.trusted_device import TrustedDevice
from ....domain.interfaces.account_repository import BaseAccountRepository
from .....building_blocks.infrastructure.persistance.exceptions import RecordNotFoundError, RecordConflictError
from ..orm.models import AccountTable, ExternalIdentityTable, TrustedDeviceTable


class SQLBaseAccountRepository(SQLBaseRepository[AccountTable], BaseAccountRepository):
    """SQLAlchemy implementation of :class:`BaseAccountRepository`."""

    def __init__(self):
        super().__init__(AccountTable)

    def _to_domain(self, record: AccountTable) -> Account:
        id = AccountId.create(record.id)

        roles = {AccountRole(r.strip()) for r in record.roles.split(",") if r.strip()}

        # Extract session IDs if available
        session_ids = []
        try:
            session_ids = [SessionId.create(s.id) for s in record.sessions]
        except Exception:
            pass

        return Account.from_data(
            id=id,
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

    # Interface implementation -------------------------------------------------
    async def add(self, account: Account) -> None:
        record = AccountTable(
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

        # AsyncSession.add is synchronous in SQLAlchemy
        self.session.add(record)

        try:
            # Flush is asynchronous and catches the DB constraints
            await self.session.flush()
        except IntegrityError:
            raise RecordConflictError(identifier=str(account.email))

    async def update(self, account: Account) -> None:
        result = await self.session.execute(
            select(AccountTable)
            .options(selectinload(AccountTable.external_identities), selectinload(AccountTable.trusted_devices))
            .filter(AccountTable.id == account.id.value)
        )
        record = result.scalars().first()
        if not record:
            raise RecordNotFoundError(identifier=str(account.id.value))

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

    async def get_by_id(self, account_id: AccountId) -> Account | None:
        stmt = (
            select(AccountTable)
            .options(
                selectinload(AccountTable.sessions),
                selectinload(AccountTable.external_identities),
                selectinload(AccountTable.trusted_devices),
            )
            .filter(AccountTable.id == account_id.value)
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        if not record:
            raise RecordNotFoundError(identifier=str(account_id.value))
        return self._to_domain(record)

    async def get_by_email(self, email: str) -> Account | None:
        stmt = (
            select(AccountTable)
            .options(
                selectinload(AccountTable.sessions),
                selectinload(AccountTable.external_identities),
                selectinload(AccountTable.trusted_devices),
            )
            .filter(AccountTable.email == email)
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        return self._to_domain(record) if record else None

    async def get_by_external_identity(self, provider: str, provider_user_id: str) -> Account | None:
        stmt = (
            select(AccountTable)
            .join(AccountTable.external_identities)
            .options(
                selectinload(AccountTable.sessions),
                selectinload(AccountTable.external_identities),
                selectinload(AccountTable.trusted_devices),
            )
            .filter(ExternalIdentityTable.provider == provider.lower())
            .filter(ExternalIdentityTable.provider_user_id == provider_user_id)
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        return self._to_domain(record) if record else None

    async def exists_by_email(self, email: str) -> bool:
        stmt = select(AccountTable.id).filter(AccountTable.email == email)
        result = await self.session.execute(stmt)
        return result.first() is not None

    async def list_accounts(self, limit: int = 100, offset: int = 0) -> tuple[Iterable[Account], int]:
        count_stmt = select(func.count()).select_from(AccountTable)
        total_result = await self.session.execute(count_stmt)
        total_count = total_result.scalar_one()

        stmt = (
            select(AccountTable)
            .options(selectinload(AccountTable.external_identities), selectinload(AccountTable.trusted_devices))
            .order_by(AccountTable.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        records = result.scalars().all()
        return [self._to_domain(record) for record in records], total_count

    async def remove(self, account_id: AccountId) -> None:
        stmt = select(AccountTable).filter(AccountTable.id == account_id.value)
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        if record:
            await self.session.delete(record)
