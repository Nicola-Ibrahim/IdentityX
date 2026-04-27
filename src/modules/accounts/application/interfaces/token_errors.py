class TokenError(Exception):
    """Base class for token-related errors."""
    pass


class TokenExpiredError(TokenError):
    """Raised when a token has expired."""
    pass


class TokenRevokedError(TokenError):
    """Raised when a token has been revoked."""
    pass


class TokenInvalidError(TokenError):
    """Raised when a token is structurally invalid or signature fails."""
    pass
