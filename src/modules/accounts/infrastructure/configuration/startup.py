from typing import Self

from .....database import SQLAlchemySettings
from .containers import AccountsDIContainer
from .settings import AccountsSettings


class AccountsStartUp:
    def __init__(self) -> None:
        self._container: AccountsDIContainer | None = None

    def initialize(self) -> Self:
        settings = AccountsSettings()
        db_settings = SQLAlchemySettings()

        config = {
            "database": db_settings.model_dump(),
            "backend": settings.model_dump(),
        }

        try:
            self._container = AccountsDIContainer(config=config)
            self._container.init_resources()
            self._container.wire(
                packages=[
                    "src.modules.accounts.application",
                    "src.modules.accounts.infrastructure",
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
