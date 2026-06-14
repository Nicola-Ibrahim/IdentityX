from abc import ABC, abstractmethod

from src.accounts.application.account.dtos.account import AccountDTO


class ListAccountsQueryService(ABC):
    @abstractmethod
    async def list_accounts(self, limit: int = 100, offset: int = 0) -> tuple[AccountDTO, ...]:
        """Query data store directly and return paged Account DTOs."""
        pass
