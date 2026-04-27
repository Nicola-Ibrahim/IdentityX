"""Password hashing interface for the users application layer.

This interface defines the contract for password hashing services. A
concrete implementation must provide methods to securely encode
passwords and verify that a plaintext password matches a hashed
representation.  Implementations live in the infrastructure layer.
"""

from abc import ABC, abstractmethod


class IPasswordHasher(ABC):
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
