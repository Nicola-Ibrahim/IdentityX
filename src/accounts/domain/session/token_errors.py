from building_blocks.domain.exceptions import DomainError


class TokenException(DomainError):
    """Base class for token-related exceptions."""

    def __init__(self, message: str = "Token error", code: str = "TokenException"):
        super().__init__(message=message, code=code, error_type="TokenException", status_code=401)


class TokenExpiredException(TokenException):
    """Raised when a token has expired."""

    def __init__(self, message: str = "Token expired"):
        super().__init__(message=message, code="TokenExpired", status_code=401)


class TokenRevokedException(TokenException):
    """Raised when a token has been revoked."""

    def __init__(self, message: str = "Token revoked"):
        super().__init__(message=message, code="TokenRevoked", status_code=401)


class TokenInvalidException(TokenException):
    """Raised when a token is structurally invalid or signature fails."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message=message, code="TokenInvalid", status_code=401)
