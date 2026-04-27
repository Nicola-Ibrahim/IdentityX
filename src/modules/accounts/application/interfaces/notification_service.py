from abc import ABC, abstractmethod


class INotificationService(ABC):
    @abstractmethod
    def send_welcome_email(self, email: str) -> None:
        """Send a welcome email to the user."""
        raise NotImplementedError

    @abstractmethod
    def send_password_reset_email(self, email: str) -> None:
        """Send a password reset email to the user."""
        raise NotImplementedError
