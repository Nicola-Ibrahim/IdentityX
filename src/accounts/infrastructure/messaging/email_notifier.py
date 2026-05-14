from accounts.application.interfaces import BaseNotificationService


class ConsoleNotificationService(BaseNotificationService):  # type: ignore[misc]
    """Logs notifications to stdout for development environments."""

    async def send_welcome_email(self, email: str) -> None:
        print(f"[accounts] Sending welcome email to {email}")

    async def send_password_reset_email(self, email: str) -> None:
        print(f"[accounts] Sending password reset email to {email}")
