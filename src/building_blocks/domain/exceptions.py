from __future__ import annotations

from dataclasses import dataclass

from .enums import ErrorCode, ErrorType
from .rule import BaseBusinessRule


@dataclass(eq=False)
class DomainException(Exception):
    """Base exception for domain-level errors."""

    message: str
    code: ErrorCode = ErrorCode.INTERNAL_ERROR
    error_type: ErrorType = ErrorType.INTERNAL_ERROR

    def __post_init__(self) -> None:
        super().__init__(self.message)


class BusinessRuleValidationException(DomainException):
    """Raised when a :class:`BaseBusinessRule` evaluation fails."""

    def __init__(self, rule: BaseBusinessRule):
        self.rule = rule
        super().__init__(message=rule.message, code=rule.code, error_type=rule.error_type)


class EntityNotFoundException(DomainException):
    """Raised when an aggregate or entity cannot be found."""

    def __init__(self, message: str = "Entity not found."):
        super().__init__(
            message=message,
            code=ErrorCode.ENTITY_NOT_FOUND,
            error_type=ErrorType.ENTITY_NOT_FOUND,
        )


class RepositoryException(DomainException):
    """Raised when the infrastructure layer reports a repository problem."""

    def __init__(self, message: str, *, code: ErrorCode | None = None):
        super().__init__(
            message=message,
            code=code or ErrorCode.INFRASTRUCTURE_FAILURE,
            error_type=ErrorType.INFRASTRUCTURE_ERROR,
        )
