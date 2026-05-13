from abc import ABC, abstractmethod


class BasePasswordHasher(ABC):
    """Abstract base class for password hashing services."""

    @abstractmethod
    def encode(self, password: str) -> str:
        """Hash a plaintext password into a secure representation.

        Args:
            password: The plaintext password supplied by the user.

        Returns:
            str: A hashed password string.
        """

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a hashed password.

        Args:
            plain_password: The plaintext password to verify.
            hashed_password: The previously hashed password to compare against.

        Returns:
            bool: True if the passwords match, False otherwise.
        """
