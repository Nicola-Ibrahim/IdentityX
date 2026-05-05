from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from .rule import BaseBusinessRule


class ValueObject(ABC, BaseModel):
    """
    Abstract base class for all Value Objects.
    Uses Pydantic V2 for validation and immutability.
    """

    # Force immutability and allow hashing for use in sets/dicts
    model_config = ConfigDict(frozen=True)

    def __composite_values__(self) -> tuple[Any, ...]:
        """Standard hook for SQLAlchemy composite columns."""
        return tuple(self.__dict__.values())

    @classmethod
    @abstractmethod
    def create(cls, *args, **kwargs) -> Any:
        """Factory method to enforce business rules during creation."""
        raise NotImplementedError

    def check_rules(self, *rules: "BaseBusinessRule") -> None:
        """Ensure that the supplied business rules hold true."""
        from .exceptions import BusinessRuleValidationException

        for rule in rules:
            if rule.is_broken():
                raise BusinessRuleValidationException(rule)
