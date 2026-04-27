from fastapi import Request, status
from fastapi.responses import JSONResponse

from .errors import APIError
from .schemas import ErrorDetail, ErrorResponse


# Global Handler
async def global_exception_handler(request: Request, error: APIError) -> JSONResponse:
    err = ErrorResponse(
        error_code=getattr(error, "error_code", "http_error"),
        message=str(error.message),
        details=[ErrorDetail(**detail) for detail in error.details],
        documentation_url=error.documentation_url,
    )

    return JSONResponse(
        content=err.model_dump(),
        status_code=getattr(err, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR),
        headers={"Content-Type": "application/problem+json", "X-Error-Code": error.error_code},
    )
