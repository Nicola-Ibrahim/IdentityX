from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str  # e.g., "validation_error"
    target: str  # e.g., "email"
    message: str  # e.g., "Invalid email format"


class ErrorResponse(BaseModel):
    error_code: str  # e.g., "invalid_request"
    message: str  # e.g., "3 validation errors occurred"
    details: list[ErrorDetail] = []
