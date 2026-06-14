import logging

from src.accounts.domain.account.account import Account
from src.accounts.domain.account.enums.account_role import AccountRole
from src.accounts.domain.account.repositories.account_repository import BaseAccountRepository
from src.accounts.domain.account.services.password_hasher import PasswordHasher
from src.accounts.domain.account.value_objects.email import Email
from src.accounts.domain.account.value_objects.password import Password

logger = logging.getLogger(__name__)


class AdminSeeder:
    """
    Automates the seeding of a default system administrator on startup.
    """

    def __init__(self, account_repo: BaseAccountRepository, password_hasher: PasswordHasher) -> None:
        self._account_repo = account_repo
        self._password_hasher = password_hasher

    async def seed(self) -> None:
        admin_email = "admin@identityx.local"
        admin_pass = "AdminPassword123!"

        try:
            exists = await self._account_repo.exists_by_email(admin_email)
            if not exists:
                logger.info(f"Seeding default administrator: {admin_email}")
                
                email_vo = Email.create(admin_email)
                password_vo = Password.create(admin_pass)
                hashed = self._password_hasher.encode(password_vo)
                
                admin = Account.register(email=email_vo, password=hashed)
                admin.assign_role(AccountRole.ADMIN)
                admin.verify()  # Allow immediate login
                
                await self._account_repo.add(admin)
                logger.info("Administrator seeded successfully.")
            else:
                logger.debug("Administrator already exists. Skipping seeding.")
        except Exception as e:
            logger.error(f"Failed to seed database: {e}", exc_info=True)
