from abc import ABC, abstractmethod
from typing import Any


class BaseModule(ABC):
    @abstractmethod
    async def execute(self, command: Any) -> Any:
        """Execute a command."""
        raise NotImplementedError

    @abstractmethod
    async def query(self, query: Any) -> Any:
        """Execute a query."""
        raise NotImplementedError
