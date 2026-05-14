from datetime import datetime
from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseSchema(BaseModel, Generic[T]):
    """Standardized API response schema for documentation and validation"""

    api_version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = True
    data: T
    meta: Optional[dict] = None
    links: Optional[dict] = None
    message: Optional[str] = None
