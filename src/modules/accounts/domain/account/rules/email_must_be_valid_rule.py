"""Business rule ensuring an email address looks valid."""

import re
from dataclasses import dataclass, field

from src.building_blocks.domain.enums import ErrorCode, ErrorType
from src.building_blocks.domain.rule import BaseBusinessRule

_EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$")


@dataclass(slots=True)
class EmailMustBeValidRule(BaseBusinessRule):
    """Check that the supplied email matches a simple regex pattern."""

    email: str
    code: ErrorCode = field(default=ErrorCode.INVALID_EMAIL_ADDRESS, init=False)
    message: str = field(default="Provided email address is not valid.", init=False)
    error_type: ErrorType = field(default=ErrorType.VALIDATION_ERROR, init=False)

    def is_broken(self) -> bool:
        return not self.email or _EMAIL_REGEX.match(self.email) is None
