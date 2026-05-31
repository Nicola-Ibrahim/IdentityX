from src.building_blocks.domain.rule import BaseBusinessRule


class HashedPasswordMustBeArgon2FormatRule(BaseBusinessRule):
    hashed_password: str
    code: str = "HashedPasswordMustBeArgon2Format"
    message: str = "Hashed password must be in valid Argon2 format."
    error_type: str = "ValidationError"

    def is_broken(self) -> bool:
        return not self.hashed_password.startswith("$argon2")
