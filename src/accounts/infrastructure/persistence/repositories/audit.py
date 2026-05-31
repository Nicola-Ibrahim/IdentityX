from src.buckets.database.repository import SQLBaseRepository

from src.accounts.domain.audit.audit_log import AuditLog
from src.accounts.domain.interfaces.audit_repository import BaseAuditRepository
from src.accounts.infrastructure.persistence.orm.audit_logs import AuditLogTable


class SQLAuditLogRepository(SQLBaseRepository[AuditLogTable], BaseAuditRepository):
    """
    SQLAlchemy implementation for storing audit logs.
    """

    def __init__(self) -> None:
        super().__init__(AuditLogTable)

    async def add(self, audit_log: AuditLog) -> None:
        """
        Persist a new audit log entry.
        """
        record = AuditLogTable(
            id=audit_log.id.value,
            account_id=str(audit_log.account_id.value) if audit_log.account_id else None,
            action=audit_log.action.value,
            ip_address=audit_log.ip_address,
            user_agent=audit_log.user_agent,
            details=audit_log.details,
            created_at=audit_log.created_at,
            updated_at=audit_log.updated_at,
        )
        self.session.add(record)
