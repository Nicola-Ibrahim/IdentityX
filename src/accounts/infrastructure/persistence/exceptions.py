from ....building_blocks.infrastructure.persistance.exceptions import (
    BaseRepositoryException,
    RepoErrorCode,
    RepoErrorType,
)


class AccountRepositoryError(BaseRepositoryException):
    """Base exception for Account repository errors."""

    pass


class AccountRecordNotFoundError(AccountRepositoryError):
    def __init__(self, account_id: str):
        super().__init__(
            code=RepoErrorCode.ENTITY_NOT_FOUND,
            description=f"Account record with ID {account_id} not found in persistence.",
            error_type=RepoErrorType.NOT_FOUND,
        )


class AccountRecordConflictError(AccountRepositoryError):
    def __init__(self, identifier: str):
        super().__init__(
            code=RepoErrorCode.CONFLICT,
            description=f"A conflict occurred for account with identifier {identifier} in persistence.",
            error_type=RepoErrorType.CONFLICT,
        )


class SessionRecordNotFoundError(AccountRepositoryError):
    def __init__(self, session_id: str):
        super().__init__(
            code=RepoErrorCode.ENTITY_NOT_FOUND,
            description=f"Session record with ID {session_id} not found in persistence.",
            error_type=RepoErrorType.NOT_FOUND,
        )
