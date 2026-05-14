from building_blocks.domain.rule import BaseBusinessRule


class RefreshTokenMustBeSecureRule(BaseBusinessRule):
    """Rule ensuring refresh tokens are sufficiently random."""

    token: str
    min_length: int = 32
    code: str = "InvalidPassword"
    message: str = "Refresh token must be secure and meet minimum length requirements"
    error_type: str = "ValidationError"

    def is_broken(self) -> bool:
        return not self.token or len(self.token) < self.min_length
