from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from .exceptions import BusinessRuleValidationException
from .rule import BaseBusinessRule


class ValueObject(ABC, BaseModel):
    """Abstract base class for value objects."""

    def __eq__(self, other: Any) -> bool:
        """Check equality based on the value object properties."""
        if not isinstance(other, ValueObject):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        """Return the hash of the value object."""
        return hash(tuple(sorted(self.__dict__.items())))

    def __str__(self) -> str:
        """Return the string representation of the value object."""
        return str(self.__dict__)

    def check_rules(self, *rules: BaseBusinessRule) -> None:
        """Ensure that the supplied business rules hold true."""
        for rule in rules:
            if rule.is_broken():
                raise BusinessRuleValidationException(rule)

    @classmethod
    @abstractmethod
    def create(cls, *args, **kwargs) -> "ValueObject":
        """Abstract method for creating the value object, enforcing rule validation."""
        raise NotImplementedError
