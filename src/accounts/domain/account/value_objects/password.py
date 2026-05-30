from typing import Self

from src.building_blocks.domain.value_object import ValueObject

from src.accounts.domain.account.rules.password_must_meet_policy_rule import PasswordMustMeetPolicyRule


class Password(ValueObject):
    value: str

    @classmethod
    def create(cls, value: str) -> Self:
        cls.check_rules(PasswordMustMeetPolicyRule(password=value))
        return cls(value=value)
