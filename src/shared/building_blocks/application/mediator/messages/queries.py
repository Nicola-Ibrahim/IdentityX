from abc import ABC, abstractmethod


class BaseQuery[TResponse]:
    """Base class for all queries."""

    pass


class BaseQueryHandler[TQuery: BaseQuery, TResponse](ABC):
    """Base class for all query handlers."""

    @abstractmethod
    async def handle(self, query: TQuery) -> TResponse:
        raise NotImplementedError
