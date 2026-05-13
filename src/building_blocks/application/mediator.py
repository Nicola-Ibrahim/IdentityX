import importlib
import inspect
import pkgutil
from abc import abstractmethod
from typing import Any, Callable, Generic, TypeVar, get_type_hints

TResponse = TypeVar("TResponse")
TCommand = TypeVar("TCommand", bound="BaseCommand")
TQuery = TypeVar("TQuery", bound="BaseQuery")

class BaseCommand(Generic[TResponse]):
    pass

class BaseQuery(Generic[TResponse]):
    pass

_handler_registry: dict[type, type] = {}

class BaseCommandHandler(Generic[TCommand, TResponse]):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        hints = get_type_hints(cls.handle)
        command_type = hints.get("command")
        if command_type and command_type is not inspect.Parameter.empty:
            _handler_registry[command_type] = cls

    @abstractmethod
    async def handle(self, command: TCommand) -> TResponse:
        raise NotImplementedError

class BaseQueryHandler(Generic[TQuery, TResponse]):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        hints = get_type_hints(cls.handle)
        query_type = hints.get("query")
        if query_type and query_type is not inspect.Parameter.empty:
            _handler_registry[query_type] = cls

    @abstractmethod
    async def handle(self, query: TQuery) -> TResponse:
        raise NotImplementedError

class Mediator:
    def __init__(self, root_package: str, behaviors: list = None) -> None:
        self._service_registry: dict[type, Callable] = {}
        self._behaviors = behaviors or []
        self._scan(root_package)

    def register_service(self, interface_type: type, factory: Callable) -> None:
        self._service_registry[interface_type] = factory

    async def execute(self, command: BaseCommand) -> Any:
        return await self._dispatch(command)

    async def query(self, query: BaseQuery) -> Any:
        return await self._dispatch(query)

    def _scan(self, root_package: str) -> None:
        pkg = importlib.import_module(root_package)
        for _, name, _ in pkgutil.walk_packages(pkg.__path__, prefix=root_package + "."):
            try:
                importlib.import_module(name)
            except Exception:
                pass

    def _resolve_handler(self, handler_class: type) -> Any:
        hints = get_type_hints(handler_class.__init__)
        kwargs = {}
        for name, hint in hints.items():
            if name == "return":
                continue
            if hint in self._service_registry:
                factory = self._service_registry[hint]
                kwargs[name] = factory() if callable(factory) else factory
        return handler_class(**kwargs)

    async def _dispatch(self, request: Any) -> Any:
        handler_class = _handler_registry.get(type(request))
        if not handler_class:
            raise LookupError(f"No handler registered for {type(request).__name__}.")
        handler = self._resolve_handler(handler_class)
        
        async def core_handler():
            return await handler.handle(request)

        pipeline = core_handler
        for behavior in reversed(self._behaviors):
            def make_step(b, next_step):
                return lambda: b.handle(request, next_step)
            pipeline = make_step(behavior, pipeline)

        return await pipeline()
