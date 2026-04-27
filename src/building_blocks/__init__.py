"""
Cross-cutting building blocks shared by every bounded context.

The package exposes reusable domain, application and infrastructure
primitives such as entities, value objects, command/query buses and
integration patterns (event bus, outbox, unit of work).  Modules should
depend downward on these building blocks to avoid circular coupling.
"""

__all__ = ["domain", "application", "infrastructure"]
