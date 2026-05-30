import re

from src.building_blocks.domain.rule import BaseBusinessRule

_EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$")


class EmailMustBeValidRule(BaseBusinessRule):
    """Check that the supplied email matches a simple regex pattern."""

    email: str
    code: str = "InvalidEmailAddress"
    message: str = "Provided email address is not valid."
    error_type: str = "ValidationError"

    def is_broken(self) -> bool:
        return not self.email or _EMAIL_REGEX.match(self.email) is None
