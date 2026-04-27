"""Command for assigning a role to an account."""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class AssignRoleCommand:
    account_id: str
    role_id: str
