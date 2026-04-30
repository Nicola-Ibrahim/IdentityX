import uuid
from dataclasses import dataclass
from typing import Self

from ......building_blocks.domain.value_object import ValueObject

@dataclass(frozen=True)
class AccountId(ValueObject):
    """
    Account identifier within the Session context.
    Provides separation from the Account context's own AccountId.
    """
    value: uuid.UUID

    @classmethod
    def create(cls, value: uuid.UUID | str | None = None) -> Self:
        if value is None:
            return cls(value=uuid.uuid4())
        if isinstance(value, str):
            return cls(value=uuid.UUID(value))
        return cls(value=value)

    def __str__(self) -> str:
        return str(self.value)
