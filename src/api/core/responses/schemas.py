from datetime import datetime
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base fields shared by all API responses."""

    api_version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse[T](BaseResponse):
    """Standardized schema for successful API responses."""

    success: bool = True
    data: T
    meta: dict | None = None
    links: dict | None = None
    message: str | None = None


class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: str
    message: str
    target: str | None = None


class FailureResponse(BaseResponse):
    """Standardized schema for error API responses."""

    success: bool = False
    errors: list[ErrorDetail]
    message: str | None = None
