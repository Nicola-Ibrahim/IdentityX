"""Messaging adapter that simulates sending account emails."""

from __future__ import annotations

from ...application.interfaces import INotificationService


class ConsoleNotificationService(INotificationService):  # type: ignore[misc]
    """Logs notifications to stdout for development environments."""

    def send_welcome_email(self, email: str) -> None:
        print(f"[accounts] Sending welcome email to {email}")

    def send_password_reset_email(self, email: str) -> None:
        print(f"[accounts] Sending password reset email to {email}")
