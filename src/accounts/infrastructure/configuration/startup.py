from typing import Self

from dependency_injector import providers

from .containers import AccountsDIContainer


class AccountsStartUp:
    def __init__(self) -> None:
        self._container: AccountsDIContainer | None = None

    def initialize(self, database: providers.Provider) -> Self:
        try:
            self._container = AccountsDIContainer(session_factory=database)
            self._container.init_resources()
            self._container.wire(
                packages=[
                    "src.accounts.application",
                    "src.accounts.infrastructure",
                    "src.api.routers.accounts",
                ]
            )
            return self
        except Exception as ex:
            raise RuntimeError("Accounts module bootstrap failed") from ex

    async def stop(self) -> None:
        try:
            if self._container:
                await self._container.stop()
        finally:
            self._container = None
