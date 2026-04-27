"""Access Control Service."""

import uuid

from ...domain.account.value_objects.account_id import AccountId
from ...domain.interfaces import AccountRepository, RoleRepository
from ...domain.role.value_objects.role_id import RoleId
from .assign_role_command import AssignRoleCommand
from .assign_role_dto import AssignedRoleDTO


class AccessControlService:
    def __init__(self, account_repo: AccountRepository, role_repo: RoleRepository) -> None:
        self._accounts = account_repo
        self._roles = role_repo

    def assign_role(self, command: AssignRoleCommand) -> AssignedRoleDTO:
        try:
            account_id = AccountId.create(uuid.UUID(command.account_id))
            role_id = RoleId.create(uuid.UUID(command.role_id))
        except (ValueError, AttributeError) as exc:
            raise ValueError("Invalid identifiers supplied") from exc

        account = self._accounts.get_by_id(account_id)
        if not account:
            raise ValueError("Account not found")
        role = self._roles.get_by_id(role_id)
        if not role:
            raise ValueError("Role not found")

        account.assign_role(role_id)
        role.emit_assigned_event(str(account.id.value))
        self._accounts.assign_role(account_id, role_id)
        self._accounts.update(account)
        return AssignedRoleDTO(account_id=str(account.id.value), role_id=str(role_id.value))
