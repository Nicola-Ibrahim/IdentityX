from passlib.context import CryptContext

from src.accounts.application.interfaces import BasePasswordHasher


class Argon2PasswordHasher(BasePasswordHasher):  # type: ignore[misc]
    """State-of-the-art password hasher using Argon2id.

    This uses passlib to handle the complex memory-hard and time-hard
    parameters of the Argon2 algorithm.
    """

    def __init__(self) -> None:
        # Argon2 is the default and only allowed algorithm for this hasher
        self._ctx = CryptContext(schemes=["argon2"], deprecated="auto")

    def encode(self, password: str) -> str:
        """Hash a password using Argon2id."""
        return self._ctx.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against an Argon2 hash."""
        return self._ctx.verify(plain_password, hashed_password)
