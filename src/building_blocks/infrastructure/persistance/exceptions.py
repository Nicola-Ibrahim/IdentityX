from dataclasses import dataclass
from enum import Enum


# Define error types for repository exceptions
class RepoErrorType(Enum):
    """Enumeration of repository error types."""

    NOT_FOUND = "NotFound"
    DATABASE_ERROR = "DatabaseError"
    CONFLICT = "Conflict"


# Define error codes for repository exceptions
class RepoErrorCode(Enum):
    """Enumeration of repository error codes."""

    NOT_FOUND = "NotFound"
    DATABASE_ERROR = "DatabaseError"
    CONFLICT = "Conflict"
    ENTITY_NOT_FOUND = "EntityNotFound"
    DB_CONNECTION_FAILED = "DbConnectionFailed"


@dataclass
class BaseRepositoryException(Exception):
    """Base class for repository-related exceptions."""

    code: RepoErrorCode
    description: str
    error_type: RepoErrorType

    def __post_init__(self):
        # Initialize the message using the code and description
        self.message = f"{self.error_type.value}: {self.code.value} - {self.description}"
        super().__init__(self.message)

    @classmethod
    def entity_not_found(cls, description: str) -> "BaseRepositoryException":
        """Create an entity not found exception."""
        return cls(RepoErrorCode.ENTITY_NOT_FOUND, description, RepoErrorType.NOT_FOUND)

    @classmethod
    def database_error(cls, description: str) -> "BaseRepositoryException":
        """Create a database error exception."""
        return cls(RepoErrorCode.DATABASE_ERROR, description, RepoErrorType.DATABASE_ERROR)

    @classmethod
    def conflict(cls, description: str) -> "BaseRepositoryException":
        """Create a conflict exception."""
        return cls(RepoErrorCode.CONFLICT, description, RepoErrorType.CONFLICT)

    @classmethod
    def db_connection_failed(cls, description: str) -> "BaseRepositoryException":
        """Create a database connection failed exception."""
        return cls(RepoErrorCode.DB_CONNECTION_FAILED, description, RepoErrorType.DATABASE_ERROR)

    def to_dict(self) -> dict:
        """
        Convert the exception details to a dictionary.

        Returns:
            dict: A dictionary containing the exception details.
        """
        return {
            "code": self.code.value,
            "description": self.description,
            "error_type": self.error_type.value,
        }


class RepositoryException(BaseRepositoryException):
    """Exception raised when there is a conflict in repository operations."""
