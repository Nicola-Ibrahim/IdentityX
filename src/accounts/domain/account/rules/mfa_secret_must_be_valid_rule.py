import re
from src.shared.building_blocks.domain.rule import BaseBusinessRule


class MfaSecretMustBeValidRule(BaseBusinessRule):
    secret: str
    code: str = "InvalidMfaSecret"
    message: str = "MFA secret must be a valid base32 string."
    error_type: str = "ValidationError"

    def is_broken(self) -> bool:
        if not self.secret:
            return True
        # Base32 regex (A-Z, 2-7, padding =)
        return not bool(re.match(r"^[A-Z2-7]+=*$", self.secret))
