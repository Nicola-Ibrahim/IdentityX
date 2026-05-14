from typing import Any
from fastapi.responses import JSONResponse

from api.core.config import get_settings
from .schemas import ResponseSchema


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
        # Build the content using the response schema for consistency
        schema = ResponseSchema(
            api_version=get_settings().API_VERSION,
            data=data,
            meta=meta,
            links=links,
            message=message,
        )

        super().__init__(
            content=schema.model_dump(mode="json"),
            status_code=status_code,
            headers={"Content-Type": "application/json", "X-API-Version": get_settings().API_VERSION},
            **kwargs,
        )
