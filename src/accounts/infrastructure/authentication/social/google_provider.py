from authlib.integrations.httpx_client import AsyncOAuth2Client
from typing import Any
from src.accounts.application.interfaces.social_provider import BaseSocialAuthenticationProvider


class GoogleAuthenticationProvider(BaseSocialAuthenticationProvider):
    """
    Google-specific implementation of the social authentication provider.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        auth_url: str,
        server_metadata_url: str,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._auth_url = auth_url
        self._metadata_url = server_metadata_url

    @property
    def provider_name(self) -> str:
        return "google"

    async def get_authorization_url(self, state: str) -> str:
        """
        Generate the Google OAuth2 authorization URL.
        """
        return (
            f"{self._auth_url}"
            "?response_type=code"
            f"&client_id={self._client_id}"
            f"&redirect_uri={self._redirect_uri}"
            f"&state={state}"
            "&scope=openid%20email%20profile"
        )

    async def fetch_profile(self, code: str) -> dict[str, Any]:
        """
        Exchange code for token and fetch Google profile info.
        """
        async with AsyncOAuth2Client(
            client_id=self._client_id,
            client_secret=self._client_secret,
        ) as client:
            await client.load_server_metadata(self._metadata_url)

            # Exchange code for token
            await client.fetch_token(
                url=client.metadata.get("token_endpoint"),
                code=code,
                redirect_uri=self._redirect_uri,
                grant_type="authorization_code",
            )

            # Fetch user info
            user_info_resp = await client.get(client.metadata.get("userinfo_endpoint"))
            user_data = user_info_resp.json()

            email = user_data.get("email")
            sub = user_data.get("sub")

            if not email or not sub:
                raise ValueError("Invalid response from Google: missing email or sub")

            return {
                "provider": self.provider_name,
                "provider_user_id": str(sub),
                "email": email,
                "name": user_data.get("name"),
                "picture_url": user_data.get("picture"),
            }
