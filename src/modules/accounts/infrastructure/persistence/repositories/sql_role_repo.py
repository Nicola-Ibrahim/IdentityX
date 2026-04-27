import uuid
from typing import Callable, Iterable, Optional

from sqlalchemy.orm import Session

from .....accounts.domain.interfaces.role_repository import RoleRepository
from .....accounts.domain.role.role import Role
from .....accounts.domain.role.value_objects.role_id import RoleId
from .....accounts.domain.role.value_objects.role_name import RoleName
from ..orm.models import RoleModel


class SQLRoleRepository(RoleRepository):
    """SQLAlchemy repository for role aggregates."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def _to_domain(self, record: RoleModel) -> Role:
        role = Role(
            _id=RoleId(uuid.UUID(record.uuid)),
            _name=RoleName.create(record.name),
            _description=record.description or "",
            _permissions=set(),
        )
        return role

    def add(self, role: Role) -> None:
        with self._session_factory() as session:  # type: Session
            record = RoleModel(uuid=str(role.id.value), name=str(role.name), description=role.description)
            session.add(record)
            session.commit()

    def get_by_id(self, role_id: RoleId) -> Optional[Role]:
        with self._session_factory() as session:  # type: Session
            record = session.query(RoleModel).filter(RoleModel.uuid == str(role_id.value)).one_or_none()
            return self._to_domain(record) if record else None

    def get_by_name(self, name: str) -> Optional[Role]:
        with self._session_factory() as session:  # type: Session
            record = session.query(RoleModel).filter(RoleModel.name == name).one_or_none()
            return self._to_domain(record) if record else None

    def list_roles(self) -> Iterable[Role]:
        with self._session_factory() as session:  # type: Session
            records = session.query(RoleModel).order_by(RoleModel.name.asc()).all()
            return [self._to_domain(record) for record in records]
