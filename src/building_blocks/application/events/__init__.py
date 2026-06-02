"""
IdentityX Event Bus — Application Layer Abstractions.

This module exposes the public contracts for domain event dispatching.
Concrete implementations live in ``building_blocks.infrastructure.events``.

Exports:
    - ``BaseEventBus``     — Abstract event bus interface (publish / publish_all).
    - ``BaseEventHandler`` — Abstract typed handler base (handle[TEvent]).
"""

from src.building_blocks.application.events.base_event_bus import BaseEventBus
from src.building_blocks.application.events.base_event_handler import BaseEventHandler

__all__ = [
    "BaseEventBus",
    "BaseEventHandler",
]
