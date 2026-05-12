from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from src.building_blocks.infrastructure.transaction import TransactionScope

class TransactionMiddleware(BaseHTTPMiddleware):
    """Opens a TransactionScope per HTTP request (= C#'s AddScoped<DbContext>)."""

    async def dispatch(self, request: Request, call_next) -> Response:
        session_factory = request.app.state.session_factory
        async with TransactionScope(session_factory):
            return await call_next(request)
