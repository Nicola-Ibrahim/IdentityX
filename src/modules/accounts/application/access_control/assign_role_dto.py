"""DTO describing an account-role assignment."""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class AssignedRoleDTO:
    account_id: str
    role_id: str
