from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..modules.accounts.infrastructure.configuration.startup import AccountsStartUp
from .core import middleware
from .core.config import get_settings
from .core.config.base import ApiSettings
from .core.exceptions.errors import APIError
from .core.exceptions.handlers import global_exception_handler
from .core.utils.routing_helpers import collect_routers


class APIFactory:
    def __init__(self):
        self.app: FastAPI | None = None

        self.settings: ApiSettings = get_settings()

    def create_app(self) -> FastAPI:
        settings = self.settings
        settings.configure()

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            startups: list[object] = []
            modules: dict[str, object] = {}
            try:
                accounts = AccountsStartUp().initialize()
                startups.append(accounts)
                modules["accounts"] = accounts
                app.state.backend_modules = modules
                yield
            finally:
                for startup in reversed(startups):
                    try:
                        await startup.stop()
                    except Exception:
                        pass

        self.app = FastAPI(
            title=settings.PROJECT_NAME,
            version=settings.VERSION,
            description=settings.DESCRIPTION,
            lifespan=lifespan,
            # docs_url=self.settings.DOCS_URL,
            # redoc_url=self.settings.REDOC_URL,
            # contact=self.settings.CONTACT_INFO,
            # license_info=self.settings.LICENSE_INFO,
            # openapi_url=self.settings.OPENAPI_URL,
        )

        self._configure_middleware()
        self._register_exception_handlers()
        self._register_routers()
        return self.app

    def run(self, **uvicorn_kwargs):
        if not self.app:
            self.create_app()
        uvicorn.run(
            app=self.app,
            host=self.settings.HOST,
            port=self.settings.PORT,
            reload=self.settings.DEBUG,
            workers=self.settings.WORKERS,
            log_level="debug" if self.settings.DEBUG else "info",
            **uvicorn_kwargs,
        )

    def _configure_middleware(self):
        self.app.add_middleware(middleware.SecurityHeadersMiddleware)
        if self.settings.CORS_ENABLED:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=self.settings.CORS_ORIGINS,
                allow_credentials=self.settings.CORS_ALLOW_CREDENTIALS,
                allow_methods=self.settings.CORS_ALLOW_METHODS,
                allow_headers=self.settings.CORS_ALLOW_HEADERS,
            )

    def _register_routers(self):
        routers = collect_routers()
        for router in routers:
            self.app.include_router(
                router,
                prefix=f"/api/{self.settings.VERSION}",
                tags=[router.tags[0]] if router.tags else None,
            )

    def _register_exception_handlers(self):
        for error in APIError.__subclasses__():
            self.app.add_exception_handler(error, global_exception_handler)
        self.app.add_exception_handler(Exception, global_exception_handler)


app = APIFactory().create_app()


if __name__ == "__main__":
    """Convenience entrypoint to start the API via APIFactory.run"""
    APIFactory().run()
