"""Value object for role identifiers."""

import uuid
from dataclasses import dataclass
from typing import Self

from src.building_blocks.domain.value_object import ValueObject


@dataclass(slots=True)
class RoleId(ValueObject):
    value: uuid.UUID

    @classmethod
    def create(cls, value: uuid.UUID | None = None) -> Self:
        return cls(value=value or uuid.uuid4())

    def __str__(self) -> str:  # pragma: no cover
        return str(self.value)
