from pydantic import Field

from building_blocks.domain.value_object import ValueObject


class ExternalIdentity(ValueObject):
    """
    Value object representing an identity from an external provider (e.g., Google, GitHub).
    """

    provider: str = Field(..., description="The name of the external provider (e.g., 'google', 'github').")
    provider_user_id: str = Field(..., description="The unique identifier provided by the external provider.")

    @classmethod
    def create(cls, provider: str, provider_user_id: str) -> "ExternalIdentity":
        # Note: We can add validation rules here if needed
        return cls(provider=provider.lower(), provider_user_id=provider_user_id)

    def __str__(self) -> str:
        return f"{self.provider}:{self.provider_user_id}"
