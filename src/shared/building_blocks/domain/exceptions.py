from dataclasses import dataclass
from src.shared.building_blocks.domain.rule import BaseBusinessRule


@dataclass(eq=False)
class DomainException(Exception):
    """Base exception for domain-level errors."""

    message: str
    code: str = "InternalError"
    error_type: str = "InternalError"
    status_code: int = 400

    def __post_init__(self) -> None:
        super().__init__(self.message)


DomainError = DomainException


class BusinessRuleValidationException(DomainException):
    """Raised when a :class:`BaseBusinessRule` evaluation fails."""

    def __init__(self, rule: BaseBusinessRule):
        self.rule = rule
        super().__init__(message=rule.message, code=rule.code, error_type=rule.error_type)


class EntityNotFoundException(DomainException):
    """Raised when an aggregate or entity cannot be found."""

    def __init__(self, message: str = "Entity not found."):
        super().__init__(message=message, code="EntityNotFound", error_type="EntityNotFound", status_code=404)


class RepositoryException(DomainException):
    """Raised when the infrastructure layer reports a repository problem."""

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(
            message=message,
            code=code or "InfrastructureFailure",
            error_type="InfrastructureError",
        )
