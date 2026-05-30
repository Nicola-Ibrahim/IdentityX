from typing import Any

from src.building_blocks.domain.entity import Entity
from src.accounts.domain.audit.audit_action import AuditAction
from src.accounts.domain.audit.value_objects.audit_log_id import AuditLogId


class AuditLog(Entity[AuditLogId]):
    """
    Domain entity representing a security-relevant audit log entry.
    """

    account_id: str | None = None
    action: AuditAction
    ip_address: str
    user_agent: str
    details: dict[str, Any] | None = None

    class Config:
        arbitrary_types_allowed = True
