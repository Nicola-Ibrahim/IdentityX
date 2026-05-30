from typing import override
from pydantic import BaseModel

from building_blocks.application.mediator import BaseQuery, BaseQueryHandler
from accounts.application.providers import SocialProviders


class GetSocialAuthUrlQuery(BaseModel, BaseQuery[str]):
    provider_name: str
    state: str


class GetSocialAuthUrlHandler(BaseQueryHandler[GetSocialAuthUrlQuery, str]):
    def __init__(self, providers: SocialProviders):
        self._providers = providers

    @override
    async def handle(self, query: GetSocialAuthUrlQuery) -> str:
        provider = self._providers.get(query.provider_name)
        if not provider:
            raise ValueError(f"Social provider '{query.provider_name}' is not supported.")
        return await provider.get_authorization_url(query.state)
