import uuid
from typing import Callable, Iterable, Optional

from sqlalchemy.orm import Session

from .....accounts.domain.account.account import Account
from .....accounts.domain.account.value_objects.account_id import AccountId
from .....accounts.domain.account.value_objects.account_status import AccountStatus
from .....accounts.domain.account.value_objects.email import Email
from .....accounts.domain.account.value_objects.hashed_password import HashedPassword
from .....accounts.domain.interfaces.account_repository import AccountRepository
from .....accounts.domain.role.value_objects.role_id import RoleId
from ..orm.models import AccountModel, CredentialModel, RoleModel


class SQLAccountRepository(AccountRepository):
    """SQLAlchemy implementation of :class:`AccountRepository`."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def _to_domain(self, record: AccountModel) -> Account:
        email = Email.create(record.email)
        account_id = AccountId(uuid.UUID(record.uuid))
        hashed = HashedPassword.create(record.credential.hashed_password)
        status = AccountStatus.create(is_verified=record.is_verified, is_active=record.is_active)
        role_ids = {RoleId(uuid.UUID(role.uuid)) for role in record.roles}
        account = Account(
            _id=account_id,
            _email=email,
            _password=hashed,
            _status=status,
            _role_ids=role_ids,
        )
        account._created_at = record.created_at  # type: ignore[attr-defined]
        account._updated_at = record.updated_at  # type: ignore[attr-defined]
        return account

    def _apply_domain(self, account: Account, record: AccountModel) -> None:
        record.email = str(account.email)
        record.is_active = account.is_active
        record.is_verified = account.is_verified
        if not record.credential:
            record.credential = CredentialModel(hashed_password=account.hashed_password.value)
        else:
            record.credential.hashed_password = account.hashed_password.value

    # Interface implementation -------------------------------------------------
    def add(self, account: Account) -> None:
        with self._session_factory() as session:  # type: Session
            record = AccountModel(
                uuid=str(account.id.value),
                email=str(account.email),
                is_verified=account.is_verified,
                is_active=account.is_active,
            )
            record.credential = CredentialModel(hashed_password=account.hashed_password.value)
            session.add(record)
            session.commit()

    def update(self, account: Account) -> None:
        with self._session_factory() as session:  # type: Session
            db_account = session.query(AccountModel).filter(AccountModel.uuid == str(account.id.value)).one_or_none()
            if not db_account:
                raise ValueError("Account not found")
            self._apply_domain(account, db_account)
            session.commit()

    def get_by_id(self, account_id: AccountId) -> Optional[Account]:
        with self._session_factory() as session:  # type: Session
            record = session.query(AccountModel).filter(AccountModel.uuid == str(account_id.value)).one_or_none()
            return self._to_domain(record) if record else None

    def get_by_email(self, email: str) -> Optional[Account]:
        with self._session_factory() as session:  # type: Session
            record = session.query(AccountModel).filter(AccountModel.email == email).one_or_none()
            return self._to_domain(record) if record else None

    def exists_by_email(self, email: str) -> bool:
        with self._session_factory() as session:  # type: Session
            return session.query(AccountModel.uuid).filter(AccountModel.email == email).first() is not None

    def list_accounts(self) -> Iterable[Account]:
        with self._session_factory() as session:  # type: Session
            records = session.query(AccountModel).order_by(AccountModel.created_at.asc()).all()
            return [self._to_domain(record) for record in records]

    def remove(self, account_id: AccountId) -> None:
        with self._session_factory() as session:  # type: Session
            record = session.query(AccountModel).filter(AccountModel.uuid == str(account_id.value)).one_or_none()
            if record:
                session.delete(record)
                session.commit()

    def assign_role(self, account_id: AccountId, role_id: RoleId) -> None:
        with self._session_factory() as session:  # type: Session
            account = session.query(AccountModel).filter(AccountModel.uuid == str(account_id.value)).one_or_none()
            role = session.query(RoleModel).filter(RoleModel.uuid == str(role_id.value)).one_or_none()
            if not account or not role:
                raise ValueError("Account or role not found")
            if role not in account.roles:
                account.roles.append(role)
            session.commit()
