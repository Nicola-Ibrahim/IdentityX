from datetime import datetime
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel):
    """Base fields shared by all API responses."""

    api_version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseResponse, Generic[T]):
    """Standardized schema for successful API responses."""

    success: bool = True
    data: T
    meta: Optional[dict] = None
    links: Optional[dict] = None
    message: Optional[str] = None


class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: str
    message: str
    target: Optional[str] = None


class FailureResponse(BaseResponse):
    """Standardized schema for error API responses."""

    success: bool = False
    errors: List[ErrorDetail]
    message: Optional[str] = None
