from dataclasses import dataclass
from typing import Self

from ......building_blocks.domain.value_object import ValueObject


@dataclass(slots=True)
class AccountStatus(ValueObject):
    is_verified: bool = False
    is_active: bool = True

    @classmethod
    def create(cls, is_verified: bool = False, is_active: bool = True) -> Self:
        return cls(is_verified=is_verified, is_active=is_active)

    def mark_verified(self) -> Self:
        return AccountStatus(is_verified=True, is_active=self.is_active)

    def activate(self) -> Self:
        return AccountStatus(is_verified=self.is_verified, is_active=True)

    def deactivate(self) -> Self:
        return AccountStatus(is_verified=self.is_verified, is_active=False)
