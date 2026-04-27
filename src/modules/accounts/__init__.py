"""Top-level package for the accounts bounded context.

This module exposes the startup initialization logic used by the
application to wire up dependencies for the accounts bounded context.
The ``AccountsStartUp`` class is responsible for instantiating the
necessary services (e.g. repositories, password hasher, notification
service) and making them available to other layers of the system.

Following domain‑driven design, the accounts bounded context encapsulates
all user management concerns including registration, authentication
and profile management. It replaces the previous ``account``,
``registrations`` and ``user_access`` modules with a single cohesive
module.
"""

from .infrastructure.configuration.startup import AccountsStartUp  # noqa: F401

__all__ = ["AccountsStartUp"]
