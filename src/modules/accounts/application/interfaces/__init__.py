"""Application layer interface definitions for the users module.

These interfaces define the contracts for services that may be provided
by the infrastructure layer, such as notification delivery and password
hashing.
"""

from .notification_service import INotificationService  # noqa: F401
from .password_hasher import IPasswordHasher  # noqa: F401
