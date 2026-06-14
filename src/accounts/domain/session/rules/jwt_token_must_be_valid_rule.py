from src.shared.building_blocks.domain.rule import BaseBusinessRule


class JwtTokenMustBeValidRule(BaseBusinessRule):
    """Rule ensuring JWT tokens are structurally valid (non-empty, minimum length)."""

    token: str
    min_length: int = 32
    code: str = "InvalidTokenFormat"
    message: str = "JWT token format is structurally invalid."
    error_type: str = "ValidationError"

    def is_broken(self) -> bool:
        if not self.token:
            return True
        if len(self.token) < self.min_length:
            return True
        if len(self.token.split(".")) != 3:
            return True
        return False
