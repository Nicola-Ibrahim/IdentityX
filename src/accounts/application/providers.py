from .interfaces.social_provider import BaseSocialAuthenticationProvider


class SocialProviders:
    """Registry for social authentication providers."""

    def __init__(self, providers: dict[str, BaseSocialAuthenticationProvider]):
        self._providers = {p.lower(): v for p, v in providers.items()}

    def get(self, name: str) -> BaseSocialAuthenticationProvider:
        return self._providers.get(name.lower())
