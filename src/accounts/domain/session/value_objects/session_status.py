from typing import Self

from .....building_blocks.domain.value_object import ValueObject


class SessionStatus(ValueObject):
    """Value object describing the lifecycle of a session."""

    is_active: bool = True

    @classmethod
    def create(cls, is_active: bool) -> Self:
        return cls(is_active=is_active)

    @classmethod
    def active(cls) -> Self:
        return cls(is_active=True)

    @classmethod
    def revoked(cls) -> Self:
        return cls(is_active=False)

    def revoke(self) -> "SessionStatus":
        return SessionStatus(is_active=False)
