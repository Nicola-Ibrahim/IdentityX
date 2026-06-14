from typing import Self

from src.shared.building_blocks.domain.value_object import ValueObject
from src.accounts.domain.session.rules.jwt_token_must_be_valid_rule import JwtTokenMustBeValidRule


class AccessToken(ValueObject):
    value: str

    @classmethod
    def create(cls, value: str) -> Self:
        cls.check_rules(JwtTokenMustBeValidRule(token=value))
        return cls(value=value)

    def __str__(self) -> str:  # pragma: no cover
        return "<access-token>"
