from abc import ABC, abstractmethod
from ..audit.audit_log import AuditLog

class BaseAuditRepository(ABC):
    @abstractmethod
    async def add(self, audit_log: AuditLog) -> None:
        """Persist a new audit log entry."""
