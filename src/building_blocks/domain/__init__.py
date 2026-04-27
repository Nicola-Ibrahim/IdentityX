"""Domain primitives shared across bounded contexts."""

from .aggregate_root import AggregateRoot
from .entity import Entity
from .events import DomainEvent
from .exceptions import (
    BusinessRuleValidationException,
    DomainException,
    EntityNotFoundException,
    RepositoryException,
)
from .rule import BaseBusinessRule
from .value_object import ValueObject

__all__ = [
    "AggregateRoot",
    "Entity",
    "DomainEvent",
    "DomainException",
    "BusinessRuleValidationException",
    "EntityNotFoundException",
    "RepositoryException",
    "BaseBusinessRule",
    "ValueObject",
]
