"""Value object representing a hashed password."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from src.building_blocks.domain.value_object import ValueObject

from ..rules.hashed_password_must_be_set_rule import HashedPasswordMustBeSetRule


@dataclass(slots=True)
class HashedPassword(ValueObject):
    value: str

    @classmethod
    def create(cls, value: str) -> Self:
        cls.check_rules(HashedPasswordMustBeSetRule(hashed_password=value))
        return cls(value=value)

    def __str__(self) -> str:  # pragma: no cover
        return "<hashed>"
