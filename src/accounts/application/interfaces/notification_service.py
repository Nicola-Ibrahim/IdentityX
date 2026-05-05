from abc import ABC, abstractmethod


class BaseNotificationService(ABC):
    @abstractmethod
    async def send_welcome_email(self, email: str) -> None:
        """Send a welcome email to the user."""
        raise NotImplementedError

    @abstractmethod
    async def send_password_reset_email(self, email: str) -> None:
        """Send a password reset email to the user."""
        raise NotImplementedError
