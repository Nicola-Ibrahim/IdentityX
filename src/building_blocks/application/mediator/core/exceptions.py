class MediatorError(Exception):
    """Base exception for mediator errors."""

    pass


class HandlerNotFoundError(MediatorError):
    """Raised when no handler is found for a request."""

    pass
