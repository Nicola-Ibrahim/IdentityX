"""Account aggregate package."""

from src.accounts.domain.account.account import Account
from src.accounts.domain.account.value_objects.account_id import AccountId
from src.accounts.domain.account.value_objects.email import Email

__all__ = ["Account", "AccountId", "Email"]
