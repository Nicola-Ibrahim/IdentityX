from typing import Self

from src.shared.building_blocks.domain.value_object import ValueObject

from src.accounts.domain.session.rules.refresh_token_must_be_secure_rule import RefreshTokenMustBeSecureRule


class RefreshToken(ValueObject):
    value: str

    @classmethod
    def create(cls, value: str) -> Self:
        cls.check_rules(RefreshTokenMustBeSecureRule(token=value))
        return cls(value=value)

    def __str__(self) -> str:  # pragma: no cover
        return "<refresh-token>"
