from typing import Iterable

from pydantic import Field

from .....building_blocks.domain.aggregate_root import AggregateRoot
from .events.role_assigned_event import RoleAssignedEvent
from .events.role_created_event import RoleCreatedEvent
from .value_objects.role_id import RoleId
from .value_objects.role_name import RoleName


class Role(AggregateRoot[RoleId]):
    _id: RoleId
    _name: RoleName
    _description: str = ""
    _permissions: set[str] = Field(default_factory=set)

    @property
    def name(self) -> RoleName:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def permissions(self) -> Iterable[str]:
        return tuple(sorted(self._permissions))

    @classmethod
    def create(cls, name: RoleName, description: str = "", permissions: Iterable[str] | None = None) -> "Role":
        role = cls(_id=RoleId.create(), _name=name, _description=description)
        if permissions:
            role._permissions.update({perm.strip() for perm in permissions if perm})
        role.record_event(RoleCreatedEvent(role_id=str(role.id.value), name=str(name)))
        return role

    def rename(self, name: RoleName) -> None:
        if self._name != name:
            self._name = name
            self.touch()

    def change_description(self, description: str) -> None:
        if self._description != description:
            self._description = description
            self.touch()

    def add_permission(self, permission: str) -> None:
        value = permission.strip()
        if value and value not in self._permissions:
            self._permissions.add(value)
            self.touch()

    def remove_permission(self, permission: str) -> None:
        if permission in self._permissions:
            self._permissions.remove(permission)
            self.touch()

    def emit_assigned_event(self, account_id: str) -> None:
        self.record_event(RoleAssignedEvent(role_id=str(self.id.value), account_id=account_id))
