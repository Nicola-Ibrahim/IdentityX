"""Infrastructure primitives shared by bounded contexts."""

from .unit_of_work import AsyncUnitOfWork

__all__ = ["AsyncUnitOfWork"]
