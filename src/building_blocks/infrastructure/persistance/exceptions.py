class BaseRepositoryException(Exception):
    """Base exception for all repository-level errors."""

    def __init__(self, code: str, description: str, error_type: str):
        self.code = code
        self.description = description
        self.error_type = error_type
        super().__init__(description)

class RecordNotFoundError(BaseRepositoryException):
    def __init__(self, identifier: str):
        super().__init__(
            code="EntityNotFound",
            description=f"Record with identifier {identifier} not found in persistence.",
            error_type="NotFound",
        )

class RecordConflictError(BaseRepositoryException):
    def __init__(self, identifier: str):
        super().__init__(
            code="Conflict",
            description=f"A conflict occurred for record with identifier {identifier} in persistence.",
            error_type="Conflict",
        )
