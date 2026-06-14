import re

from src.shared.building_blocks.domain.rule import BaseBusinessRule

_EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$")


class EmailMustBeValidRule(BaseBusinessRule):
    """Check that the supplied email matches a simple regex pattern and meets RFC limits."""

    email: str
    code: str = "InvalidEmailAddress"
    message: str = "Provided email address is not valid or exceeds maximum length."
    error_type: str = "ValidationError"

    def is_broken(self) -> bool:
        if not self.email or len(self.email) > 254:
            return True
        return _EMAIL_REGEX.match(self.email) is None
