"""Application layer interface definitions for the users module.

These interfaces define the contracts for services that may be provided
by the infrastructure layer, such as notification delivery and password
hashing.
"""

from .notification_service import BaseNotificationService  # noqa: F401
from .password_hasher import BasePasswordHasher  # noqa: F401
from .social_provider import BaseSocialAuthenticationProvider  # noqa: F401
