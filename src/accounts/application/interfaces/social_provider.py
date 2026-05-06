from abc import ABC, abstractmethod
from typing import Any


class BaseSocialAuthenticationProvider(ABC):
    """
    Interface for social authentication providers (e.g., Google, GitHub).
    Infrastructure-specific implementations should inherit from this class.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Returns the unique identifier for this provider (e.g., 'google', 'github').
        """
        pass

    @abstractmethod
    async def get_authorization_url(self, state: str) -> str:
        """
        Generates the OAuth2 authorization URL including the CSRF state token.
        """
        pass

    @abstractmethod
    async def fetch_profile(self, code: str) -> dict[str, Any]:
        """
        Exchanges the authorization code for a token and fetches the normalized user profile.
        """
        pass
