from typing import Any, Callable
from lagom import Container

from src.shared.building_blocks.application.mediator.core.behaviors import BaseBehavior
from src.shared.building_blocks.application.mediator.core.exceptions import HandlerNotFoundError
from src.shared.building_blocks.application.mediator.messages.commands import BaseCommand
from src.shared.building_blocks.application.mediator.messages.queries import BaseQuery
from src.shared.building_blocks.application.mediator.core.scanner import discover_command_handlers



class Mediator:
    """
    Lightweight, in-process CQRS Mediator.

    Responsibilities (strict 1-to-1):
      - ``execute(command)``  → dispatches a ``BaseCommand`` to its single handler.
      - ``query(query)``      → dispatches a ``BaseQuery`` to its single handler.

    Domain event dispatching (1-to-many) is intentionally **not** the
    Mediator's responsibility.  Use ``BaseEventBus`` / ``LocalEventBus`` for
    domain events.

    Pipeline behaviors (logging, validation, transactions) are applied around
    every command/query dispatch via the ``behaviors`` list.
    """

    def __init__(
        self,
        container: Container,
        behaviors: list[BaseBehavior] | None = None,
    ) -> None:
        """
        Parameters
        ----------
        container:
            A ``Container`` instance.
        behaviors:
            Optional pipeline behaviors (e.g. ``TransactionBehavior``)
            applied around every dispatch.
        """
        self._container = container
        self._command_registry = discover_command_handlers()
        self._behaviors = behaviors or []

    def set_container(self, container: Container) -> None:
        """Replace the container after construction."""
        self._container = container

    async def execute[TResponse](self, command: BaseCommand[TResponse]) -> TResponse:
        return await self._dispatch(command)

    async def query[TResponse](self, query: BaseQuery[TResponse]) -> TResponse:
        return await self._dispatch(query)

    async def _dispatch(self, request: Any) -> Any:
        if self._container is None:
            raise RuntimeError(
                "Mediator: Container is not set. "
                "Pass a container during initialization or call set_container()."
            )

        handler_type = self._command_registry.get(type(request))
        if not handler_type:
            raise HandlerNotFoundError(f"No handler registered for request type: {type(request).__name__}")

        handler = self._container[handler_type]

        async def core_handler() -> Any:
            return await handler.handle(request)

        pipeline = core_handler
        for behavior in reversed(self._behaviors):
            pipeline = self._wrap_behavior(behavior, request, pipeline)

        return await pipeline()

    def _wrap_behavior(self, behavior: BaseBehavior, request: Any, next_call: Callable[[], Any]) -> Callable[[], Any]:
        return lambda: behavior.handle(request, next_call)



