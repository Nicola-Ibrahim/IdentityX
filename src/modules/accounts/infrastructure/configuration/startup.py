from .containers import AccountsDIContainer
from .database.session import SQLAlchemySessionFactory
from .settings import AccountsSettings


class AccountsStartUp:
    def __init__(self) -> None:
        self._container: AccountsDIContainer | None = None
        self._session_factory = None
        self._database_url = None

    @property
    def container(self) -> AccountsDIContainer:
        if self._container is None:
            raise RuntimeError("Accounts container not initialized")
        return self._container

    def initialize(
        self,
        *,
        database_url: str,
    ) -> "AccountsStartUp":
        if not database_url:
            raise ValueError("Accounts configuration requires a 'database_url'")

        self._database_url = database_url
        settings = AccountsSettings()

        config = {
            "enable_registration": settings.ENABLE_REGISTRATION,
            "default_role": settings.DEFAULT_ROLE,
            "jwt_private_key": settings.JWT_PRIVATE_KEY,
            "jwt_public_key": settings.JWT_PUBLIC_KEY,
            "jwt_algorithm": settings.JWT_ALGORITHM,
            "jwt_issuer": settings.JWT_ISSUER,
            "jwt_access_token_expire_minutes": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
            "jwt_refresh_token_expire_days": settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
        }

        try:
            self._session_factory = SQLAlchemySessionFactory.acquire(database_url)
            self._container = AccountsDIContainer(config=config, session_factory=self._session_factory)
            self._container.init_resources()
            self._container.wire(
                packages=[
                    "src.modules.accounts.application",
                    "src.modules.accounts.infrastructure",
                ]
            )
            return self
        except Exception as ex:
            raise RuntimeError("Accounts module bootstrap failed") from ex

    def stop(self) -> None:
        try:
            if self._container:
                self._container.shutdown_resources()
                self._container.unwire()
        finally:
            SQLAlchemySessionFactory.release(self._database_url)
            self._container = None
