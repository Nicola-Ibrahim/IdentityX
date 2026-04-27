from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from src.building_blocks.domain.value_object import ValueObject

from ..rules.email_must_be_valid_rule import EmailMustBeValidRule


@dataclass(slots=True)
class Email(ValueObject):
    """Email value object used by the account aggregate."""

    value: str

    @classmethod
    def create(cls, value: str) -> Self:
        cls.check_rules(EmailMustBeValidRule(email=value))
        return cls(value=value.lower().strip())

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value
