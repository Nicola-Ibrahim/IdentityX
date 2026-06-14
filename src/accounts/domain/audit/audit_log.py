from typing import Any
from src.shared.building_blocks.domain.entity import Entity
from src.accounts.domain.audit.audit_action import AuditAction
from src.accounts.domain.audit.value_objects.audit_log_id import AuditLogId
from src.accounts.domain.account.value_objects.account_id import AccountId
from src.accounts.domain.account.rules.ip_address_must_be_valid_rule import IpAddressMustBeValidRule
from src.accounts.domain.account.rules.user_agent_must_be_valid_rule import UserAgentMustBeValidRule


class AuditLog(Entity[AuditLogId]):
    """
    Domain entity representing a security-relevant audit log entry.
    """

    account_id: AccountId | None = None
    action: AuditAction
    ip_address: str
    user_agent: str
    details: dict[str, Any] | None = None

    @classmethod
    def create(
        cls,
        action: AuditAction,
        ip_address: str,
        user_agent: str,
        account_id: AccountId | None = None,
        details: dict[str, Any] | None = None,
    ) -> "AuditLog":
        """Factory method to enforce encapsulation and validation rules upon creation."""
        cls.check_rules(
            IpAddressMustBeValidRule(ip_address=ip_address),
            UserAgentMustBeValidRule(user_agent=user_agent),
        )
        return cls(
            id=AuditLogId.create(),
            account_id=account_id,
            action=action,
            ip_address=ip_address.strip(),
            user_agent=user_agent.strip(),
            details=details,
        )

    class Config:
        arbitrary_types_allowed = True
