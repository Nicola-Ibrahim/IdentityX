from src.building_blocks.domain.rule import BaseBusinessRule


class SessionCannotBeRevokedIfAlreadyInactiveRule(BaseBusinessRule):
    is_active: bool
    code: str = "SessionAlreadyInactive"
    message: str = "Session is already inactive or revoked."
    error_type: str = "DomainValidationError"

    def is_broken(self) -> bool:
        return not self.is_active
