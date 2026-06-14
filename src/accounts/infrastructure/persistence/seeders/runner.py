from src.shared.infrastructure.di.hosted_service import HostedService
from src.accounts.domain.account.repositories.account_repository import BaseAccountRepository
from src.accounts.domain.account.services.password_hasher import PasswordHasher
from src.accounts.infrastructure.persistence.seeders.admin_seeder import AdminSeeder


class AccountsSeederHostedService(HostedService):
    """
    Runs module-specific data seeders within the hosted service startup pipeline.
    """

    def __init__(self, account_repo: BaseAccountRepository, password_hasher: PasswordHasher) -> None:
        self._account_repo = account_repo
        self._password_hasher = password_hasher

    async def start(self) -> None:
        seeder = AdminSeeder(self._account_repo, self._password_hasher)
        await seeder.seed()
