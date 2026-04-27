from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from .enums import ErrorCode, ErrorType


class BaseBusinessRule(ABC, BaseModel):
    """Base type for business rules enforced by entities and value objects."""

    code: ErrorCode = Field(default=ErrorCode.BUSINESS_RULE_VIOLATION, init=False)
    message: str = Field(default="Business rule violated.", init=False)
    error_type: ErrorType = Field(default=ErrorType.BUSINESS_RULE_VIOLATION, init=False)

    @abstractmethod
    def is_broken(self) -> bool:
        """Check if the business rule is satisfied."""
