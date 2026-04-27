from typing import Optional

from fastapi import HTTPException, status


class APIError(HTTPException):
    def __init__(self, status_code: int, error_code: str, message: str, details: Optional[list[dict]] = None):
        super().__init__(status_code=status_code, detail=message)
        self.error_code = error_code
        self.details = details or []
        self.documentation_url = f"https://docs.example.com/errors#{error_code}"


class ValidationError(APIError):
    def __init__(self, message: str, details: list[dict]):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="validation_error",
            message=message,
            details=details,
        )


class NotFoundError(APIError):
    """Error for resource not found cases"""

    def __init__(self, message: str = "Resource not found", details: Optional[list[dict]] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, error_code="not_found", message=message, details=details
        )


class InternalServerError(APIError):
    """Error for unexpected server issues"""

    def __init__(self, message: str = "Internal server error", details: Optional[list[dict]] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="internal_error",
            message=message,
            details=details,
        )
