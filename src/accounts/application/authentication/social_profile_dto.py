from pydantic import BaseModel


class SocialUserProfileDTO(BaseModel):
    """
    Standardized Data Transfer Object for social user profiles.
    Used to shield the application layer from provider-specific data structures.
    """
    provider: str
    provider_user_id: str
    email: str
    name: str | None = None
    picture_url: str | None = None
