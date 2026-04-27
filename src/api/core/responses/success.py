from typing import Any, Optional

from fastapi.responses import JSONResponse

from .schemas import BaseResponse


class APIResponse(JSONResponse):
    """Standardized API success response that auto-converts to JSONResponse"""

    def __init__(
        self,
        *,
        data: Optional[Any] = None,
        meta: Optional[dict] = None,
        links: Optional[dict] = None,
        message: Optional[str] = None,
        status_code: int = 200,
        version: str = "v1",
        **kwargs,
    ):
        # Build the response data
        response_data = BaseResponse(api_version=version, success=True, data=data, meta=meta, links=links)

        if message:
            response_data.message = message

        # Initialize JSONResponse directly
        super().__init__(
            content=response_data.model_dump(),
            status_code=status_code,
            headers={"Content-Type": "application/json", "X-API-Version": version},
            **kwargs,
        )
