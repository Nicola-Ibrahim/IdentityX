import uuid
from typing import Self

from src.building_blocks.domain.value_object import ValueObject


class AuditLogId(ValueObject):
    value: uuid.UUID

    @classmethod
    def create(cls, value: uuid.UUID | None = None) -> Self:
        return cls(value=value or uuid.uuid4())

    def __str__(self) -> str:
        return str(self.value)
