from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """Base response schema for all successful API responses"""

    api_version: str = Field(..., example="v1")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = Field(..., example=True)
    data: Optional[T] = None
    meta: Optional[dict] = Field(None, example={"pagination": {"total": 100, "page": 1, "per_page": 25}})
    links: Optional[dict] = Field(None, example={"self": "/items", "next": "/items?page=2", "prev": None})

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
