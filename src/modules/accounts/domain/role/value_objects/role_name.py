"""Value object for role names."""

from dataclasses import dataclass
from typing import Self

from src.building_blocks.domain.enums import ErrorCode, ErrorType
from src.building_blocks.domain.rule import BaseBusinessRule
from src.building_blocks.domain.value_object import ValueObject


class RoleNameCannotBeEmptyRule(BaseBusinessRule):
    message = "Role name cannot be empty."
    code = ErrorCode.INVALID_INPUT
    error_type = ErrorType.VALIDATION_ERROR

    def __init__(self, value: str) -> None:
        self.value = value

    def is_broken(self) -> bool:
        return not self.value or not self.value.strip()


@dataclass(slots=True)
class RoleName(ValueObject):
    value: str

    @classmethod
    def create(cls, value: str) -> Self:
        cls.check_rules(RoleNameCannotBeEmptyRule(value))
        return cls(value=value.strip())

    def __str__(self) -> str:  # pragma: no cover
        return self.value
