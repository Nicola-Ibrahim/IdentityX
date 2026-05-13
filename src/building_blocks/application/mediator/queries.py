from abc import abstractmethod
from typing import Generic, TypeVar

TResponse = TypeVar("TResponse")
TQuery = TypeVar("TQuery", bound="BaseQuery")

class BaseQuery(Generic[TResponse]):
    """Base class for all queries."""
    pass

class BaseQueryHandler(Generic[TQuery, TResponse]):
    """Base class for all query handlers."""
    @abstractmethod
    async def handle(self, query: TQuery) -> TResponse:
        raise NotImplementedError
