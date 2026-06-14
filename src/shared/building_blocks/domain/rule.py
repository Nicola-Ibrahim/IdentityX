from abc import ABC, abstractmethod
from pydantic import BaseModel


class BaseBusinessRule(ABC, BaseModel):
    """Base type for business rules enforced by entities and value objects."""

    code: str
    message: str
    error_type: str

    @abstractmethod
    def is_broken(self) -> bool:
        """Check if the business rule is satisfied."""
