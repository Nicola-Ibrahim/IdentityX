from enum import StrEnum


class AccountRole(StrEnum):
    """Enumeration of account roles within the system."""

    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"
    GUEST = "guest"

    @classmethod
    def from_str(cls, value: str) -> "AccountRole":
        try:
            return cls(value.lower())
        except ValueError:
            return cls.USER
