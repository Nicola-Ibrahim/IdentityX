"""Account aggregate package."""

from .account import Account
from .value_objects.account_id import AccountId
from .value_objects.email import Email

__all__ = ["Account", "AccountId", "Email"]
