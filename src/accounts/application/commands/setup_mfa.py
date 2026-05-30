from typing import override
import uuid

import pyotp
from pydantic import BaseModel

from src.building_blocks.application.mediator import BaseCommand, BaseCommandHandler
from src.accounts.domain.account.value_objects.account_id import AccountId
from src.accounts.domain.interfaces.account_repository import BaseAccountRepository
from src.accounts.application.dtos.auth import MfaSetup
from src.accounts.application.interfaces.jwt import TokenService


class SetupMfaCommand(BaseModel, BaseCommand[MfaSetup]):
    mfa_token: str


class SetupMfaHandler(BaseCommandHandler[SetupMfaCommand, MfaSetup]):
    def __init__(self, token_service: TokenService, account_repo: BaseAccountRepository):
        self._token_service = token_service
        self._account_repo = account_repo

    @override
    async def handle(self, command: SetupMfaCommand) -> MfaSetup:
        claims = self._token_service.validate_mfa_token(command.mfa_token)
        account = await self._account_repo.get_by_id(AccountId.create(uuid.UUID(claims.sub)))
        if not account:
            raise ValueError("Account not found")

        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=str(account.email), issuer_name="IdentityX")

        recovery_codes = [str(uuid.uuid4())[:8] for _ in range(8)]

        return MfaSetup(secret=secret, provisioning_uri=provisioning_uri, recovery_codes=recovery_codes)
