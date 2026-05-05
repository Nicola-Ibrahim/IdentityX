from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from ..startup import IdentityXStartUp
from .core import middleware
from .core.exceptions.errors import APIError
from .core.exceptions.handlers import global_exception_handler
from .core.utils.routing_helpers import collect_routers


class APIFactory:
    def __init__(self):
        self.app: FastAPI | None = None

        self.settings = get_settings()

    def create_app(self) -> FastAPI:
        self.settings.configure()
        startup = IdentityXStartUp()

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            try:
                await startup.initialize()

                app.state.startup = startup
                # Keep compatibility with current app.state.backend_modules if needed
                app.state.backend_modules = {"accounts": startup.accounts}
                yield
            finally:
                await startup.stop()

        self.app = FastAPI(
            title=self.settings.PROJECT_NAME,
            version=self.settings.VERSION,
            description=self.settings.DESCRIPTION,
            lifespan=lifespan,
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
                prefix=f"/{self.settings.API_VERSION}",
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
