from typing import Self

from src.shared.building_blocks.domain.value_object import ValueObject


class Status(ValueObject):
    is_verified: bool = False
    is_active: bool = True

    @classmethod
    def create(cls, is_verified: bool = False, is_active: bool = True) -> Self:
        return cls(is_verified=is_verified, is_active=is_active)

    def verify(self) -> Self:
        return Status(is_verified=True, is_active=self.is_active)

    def activate(self) -> Self:
        return Status(is_verified=self.is_verified, is_active=True)

    def deactivate(self) -> Self:
        return Status(is_verified=self.is_verified, is_active=False)

    def suspend(self) -> Self:
        return self.deactivate()
