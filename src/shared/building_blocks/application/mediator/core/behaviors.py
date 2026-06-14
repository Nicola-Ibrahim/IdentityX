from typing import Any, Callable, Protocol


class BaseBehavior(Protocol):
    async def handle(self, request: Any, next_behavior: Callable[[], Any]) -> Any: ...
