from src.shared.infrastructure.database.repository import SQLBaseRepository

from src.accounts.domain.audit.audit_log import AuditLog
from src.accounts.domain.audit.repositories.audit_repository import BaseAuditRepository
from src.accounts.infrastructure.persistence.tables.audit_logs import AuditLogTable
from src.accounts.infrastructure.persistence.mappers.audit_mapper import AuditMapper


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
        record = AuditMapper.to_record(audit_log)
        self.session.add(record)
