"""Refresh token value object."""

from dataclasses import dataclass
from typing import Self

from src.building_blocks.domain.value_object import ValueObject

from ..rules.refresh_token_must_be_secure_rule import RefreshTokenMustBeSecureRule


@dataclass(slots=True)
class RefreshToken(ValueObject):
    value: str

    @classmethod
    def create(cls, value: str) -> Self:
        cls.check_rules(RefreshTokenMustBeSecureRule(token=value))
        return cls(value=value)

    def __str__(self) -> str:  # pragma: no cover
        return "<refresh-token>"
