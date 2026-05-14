from typing import Any
from fastapi.routing import APIRoute
from api.core.responses import ResponseSchema


class StandardAPIRoute(APIRoute):
    """
    Custom route class that automatically wraps the response_model in a ResponseSchema
    for OpenAPI documentation purposes.
    """

    def __init__(self, path: str, endpoint: Any, *, response_model: Any = None, **kwargs) -> None:
        if response_model:
            response_model = ResponseSchema[response_model]
        super().__init__(path, endpoint, response_model=response_model, **kwargs)
