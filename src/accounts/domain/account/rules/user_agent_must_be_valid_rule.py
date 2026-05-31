from src.building_blocks.domain.rule import BaseBusinessRule


class UserAgentMustBeValidRule(BaseBusinessRule):
    user_agent: str
    code: str = "InvalidUserAgent"
    message: str = "User agent must not be empty and must not exceed 512 characters."
    error_type: str = "ValidationError"

    def is_broken(self) -> bool:
        if not self.user_agent:
            return True
        if len(self.user_agent) > 512:
            return True
        return False
