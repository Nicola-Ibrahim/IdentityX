from typing import Any

from src.accounts.domain.audit.audit_action import AuditAction
from src.accounts.domain.audit.audit_log import AuditLog
from src.accounts.domain.account.value_objects.account_id import AccountId


class AuditService:
    """
    Application service for recording security audit logs.
    """

    def __init__(self) -> None:
        pass

    def create_entry(
        self,
        action: AuditAction,
        ip_address: str,
        user_agent: str,
        account_id: AccountId | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """
        Create a new audit log entry entity.
        The caller is responsible for persisting it via the appropriate repository.
        """
        return AuditLog.create(
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            account_id=account_id,
            details=details,
        )
