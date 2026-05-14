from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError

from api.core.responses import APIErrorResponse, ErrorDetail

from .errors import APIError


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> APIErrorResponse:
    """Handles FastAPI/Pydantic validation errors."""
    return APIErrorResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Validation failed",
        errors=[
            ErrorDetail(
                code="validation_error",
                message=err["msg"],
                target=".".join(str(p) for p in err["loc"][1:]) if len(err["loc"]) > 1 else str(err["loc"][0]),
            )
            for err in exc.errors()
        ],
    )


async def api_exception_handler(request: Request, exc: APIError) -> APIErrorResponse:
    """Handles custom domain/API errors."""
    return APIErrorResponse(
        status_code=exc.status_code,
        message=exc.detail,
        errors=[
            ErrorDetail(
                code=detail.get("code", exc.error_code),
                message=detail.get("message", exc.detail),
                target=detail.get("target"),
            )
            for detail in exc.details
        ]
        if exc.details
        else [ErrorDetail(code=exc.error_code, message=exc.detail)],
        error_code=exc.error_code,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> APIErrorResponse:
    """Handles standard FastAPI HTTPExceptions."""
    return APIErrorResponse(
        status_code=exc.status_code,
        message=str(exc.detail),
        errors=[ErrorDetail(code="http_error", message=str(exc.detail))],
    )


async def system_exception_handler(request: Request, exc: Exception) -> APIErrorResponse:
    """Handles all other unexpected system errors."""
    return APIErrorResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="An unexpected system error occurred",
        errors=[ErrorDetail(code="internal_error", message=str(exc))],
    )
