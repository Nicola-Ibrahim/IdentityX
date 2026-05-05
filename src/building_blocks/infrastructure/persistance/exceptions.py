from enum import StrEnum
from dataclasses import dataclass

class RepoErrorCode(StrEnum):
    """Enumeration of repository-level error codes."""
    ENTITY_NOT_FOUND = "EntityNotFound"
    CONFLICT = "Conflict"
    INFRASTRUCTURE_FAILURE = "InfrastructureFailure"

class RepoErrorType(StrEnum):
    """Enumeration of repository-level error types."""
    NOT_FOUND = "NotFound"
    CONFLICT = "Conflict"
    INFRASTRUCTURE_ERROR = "InfrastructureError"

@dataclass(eq=False)
class BaseRepositoryException(Exception):
    """Base exception for all repository-level errors."""
    code: RepoErrorCode
    description: str
    error_type: RepoErrorType

    def __post_init__(self) -> None:
        super().__init__(self.description)
