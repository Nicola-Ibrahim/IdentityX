from typing import Any

from ...domain.audit.audit_action import AuditAction
from ...domain.audit.audit_log import AuditLog
from ...domain.audit.value_objects.audit_log_id import AuditLogId
from ...domain.interfaces.uow import BaseAsyncUnitOfWork


class AuditService:
    """
    Application service for recording security audit logs.
    """

    def __init__(self, uow: BaseAsyncUnitOfWork) -> None:
        self.uow = uow

    async def log(
        self,
        action: AuditAction,
        ip_address: str,
        user_agent: str,
        account_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Create and persist an audit log entry.
        Note: This depends on an active transaction in the UoW.
        """
        entry = AuditLog(
            id=AuditLogId.create(),
            account_id=account_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )
        # We assume the UoW has the audit_logs property at runtime
        await self.uow.audit_logs.add(entry)
