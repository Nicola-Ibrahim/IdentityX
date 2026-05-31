from pwdlib import PasswordHash

from src.accounts.domain.account.value_objects.password import Password
from src.accounts.domain.account.value_objects.hashed_password import HashedPassword


class PasswordHasher:
    """State-of-the-art password hasher using Argon2.

    This uses pwdlib to handle hashing and verification of passwords
    via recommended Argon2id algorithms.
    """

    def __init__(self) -> None:
        self._hasher = PasswordHash.recommended()

    def encode(self, password: Password) -> HashedPassword:
        """Hash a password using Argon2."""
        return HashedPassword.create(self._hasher.hash(password.value))

    def verify(self, plain_password: Password, hashed_password: HashedPassword) -> bool:
        """Verify a password against an Argon2 hash."""
        return self._hasher.verify(plain_password.value, hashed_password.value)
