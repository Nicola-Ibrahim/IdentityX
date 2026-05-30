from typing import Any

from fastapi.responses import JSONResponse

from src.api.core.config import get_settings

from src.api.core.responses.schemas import FailureResponse, SuccessResponse


class APIResponse(JSONResponse):
    """
    Handles successful API responses only.
    Strictly uses the SuccessResponse schema.
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
        schema = SuccessResponse(
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


class APIErrorResponse(JSONResponse):
    """
    Handles error API responses only.
    Strictly uses the FailureResponse schema.
    """

    def __init__(
        self,
        *,
        errors: list[Any],
        message: str | None = None,
        status_code: int = 400,
        error_code: str = "error",
        **kwargs,
    ):
        schema = FailureResponse(
            api_version=get_settings().API_VERSION,
            errors=errors,
            message=message,
        )

        super().__init__(
            content=schema.model_dump(mode="json"),
            status_code=status_code,
            headers={
                "Content-Type": "application/json",
                "X-API-Version": get_settings().API_VERSION,
                "X-Error-Code": error_code,
            },
            **kwargs,
        )
