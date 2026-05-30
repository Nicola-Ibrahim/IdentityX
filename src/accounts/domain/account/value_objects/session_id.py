import uuid
from typing import Self

from src.building_blocks.domain.value_object import ValueObject


class SessionId(ValueObject):
    """
    Session identifier within the Account context.
    Provides separation from the Session context's own SessionId.
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
