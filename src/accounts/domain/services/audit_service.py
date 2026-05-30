from typing import Any

from src.accounts.domain.audit.audit_action import AuditAction
from src.accounts.domain.audit.audit_log import AuditLog
from src.accounts.domain.audit.value_objects.audit_log_id import AuditLogId


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
        account_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """
        Create a new audit log entry entity.
        The caller is responsible for persisting it via the appropriate repository.
        """
        return AuditLog(
            id=AuditLogId.create(),
            account_id=account_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )
