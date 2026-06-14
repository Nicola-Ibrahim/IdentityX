from src.accounts.domain.audit.audit_log import AuditLog
from src.accounts.infrastructure.persistence.tables.audit_logs import AuditLogTable


class AuditMapper:
    @staticmethod
    def to_record(audit_log: AuditLog) -> AuditLogTable:
        return AuditLogTable(
            id=audit_log.id.value,
            account_id=str(audit_log.account_id.value) if audit_log.account_id else None,
            action=audit_log.action.value,
            ip_address=audit_log.ip_address,
            user_agent=audit_log.user_agent,
            details=audit_log.details,
            created_at=audit_log.created_at,
            updated_at=audit_log.updated_at,
        )
