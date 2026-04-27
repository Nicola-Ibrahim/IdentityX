from dataclasses import dataclass
from typing import Self

from ......building_blocks.domain.value_object import ValueObject
from ..rules.password_must_meet_policy_rule import PasswordMustMeetPolicyRule


@dataclass(slots=True)
class Password(ValueObject):
    value: str

    @classmethod
    def create(cls, value: str) -> Self:
        cls.check_rules(PasswordMustMeetPolicyRule(password=value))
        return cls(value=value)
