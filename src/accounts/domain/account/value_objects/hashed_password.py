from typing import Self

from src.shared.building_blocks.domain.value_object import ValueObject
from src.accounts.domain.account.rules.hashed_password_must_be_set_rule import HashedPasswordMustBeSetRule
from src.accounts.domain.account.rules.hashed_password_must_be_argon2_format_rule import HashedPasswordMustBeArgon2FormatRule


class HashedPassword(ValueObject):
    value: str

    @classmethod
    def create(cls, value: str) -> Self:
        cls.check_rules(
            HashedPasswordMustBeSetRule(hashed_password=value),
            HashedPasswordMustBeArgon2FormatRule(hashed_password=value),
        )
        return cls(value=value)

    def __str__(self) -> str:  # pragma: no cover
        return "<hashed>"
