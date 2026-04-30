from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..config import get_settings

T = TypeVar("T")


class ResponseEnvelope(BaseModel, Generic[T]):
    """Standardized API response envelope for documentation and validation"""

    api_version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = True
    data: T
    meta: Optional[dict] = None
    links: Optional[dict] = None
    message: Optional[str] = None


class APIResponse(JSONResponse):
    """
    Standardized API response that auto-converts to JSONResponse while maintaining
    the ResponseEnvelope structure.
    """

    def __init__(
        self,
        *,
        data: Any,
        meta: dict | None = None,
        links: dict | None = None,
        message: str | None = None,
        status_code: int = 200,
        **kwargs,
    ):
        # Build the content using the envelope schema for consistency
        envelope = ResponseEnvelope(
            api_version=get_settings().API_VERSION,
            data=data,
            meta=meta,
            links=links,
            message=message,
        )

        super().__init__(
            content=envelope.model_dump(mode="json"),
            status_code=status_code,
            headers={"Content-Type": "application/json", "X-API-Version": get_settings().API_VERSION},
            **kwargs,
        )
