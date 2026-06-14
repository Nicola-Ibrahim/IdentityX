"""
IdentityX Event Bus — Infrastructure Layer Implementations.

Exports:
    - ``LocalEventBus`` — In-memory 1-to-many event bus (auto-discovers handlers).
"""

from src.shared.infrastructure.events.local_event_bus import LocalEventBus

__all__ = [
    "LocalEventBus",
]
