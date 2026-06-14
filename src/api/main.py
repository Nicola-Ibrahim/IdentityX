from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from lagom import Container

from src.api.core import middleware
from src.api.core.config import get_settings
from src.api.core.exceptions import (
    APIError,
    api_exception_handler,
    http_exception_handler,
    system_exception_handler,
    validation_exception_handler,
)
from src.api.core.security.dependencies import deps
from src.api.core.utils.routing_helpers import collect_routers
from src.application import bootstrap_application


class APIFactory:
    def __init__(self):
        self.app: FastAPI | None = None

        self.settings = get_settings()

    def create_app(self) -> FastAPI:
        self.settings.configure()

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup: Initialize composition root resources
            async with bootstrap_application() as container:
                # Bind the initialized container to the FastAPI integration helper
                deps._container = container
                yield
            # Shutdown: Resources are disposed. Reset to a fresh container for garbage collection & test isolation.
            deps._container = Container()

        app = FastAPI(
            title=self.settings.PROJECT_NAME,
            version=self.settings.VERSION,
            description=self.settings.DESCRIPTION,
            lifespan=lifespan,
        )

        self._configure_middleware(app)
        self._register_exception_handlers(app)
        self._register_routers(app)
        self.app = app
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

    def _configure_middleware(self, app: FastAPI):
        app.add_middleware(middleware.SecurityHeadersMiddleware)
        if self.settings.CORS_ENABLED:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=self.settings.CORS_ORIGINS,
                allow_credentials=self.settings.CORS_ALLOW_CREDENTIALS,
                allow_methods=self.settings.CORS_ALLOW_METHODS,
                allow_headers=self.settings.CORS_ALLOW_HEADERS,
            )

    def _register_routers(self, app: FastAPI):
        routers = collect_routers()
        for router in routers:
            app.include_router(
                router,
                prefix=f"/{self.settings.API_VERSION}",
                tags=[router.tags[0]] if router.tags else None,
            )

    def _register_exception_handlers(self, app: FastAPI):
        app.add_exception_handler(APIError, api_exception_handler)  # type: ignore
        app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore
        app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore
        app.add_exception_handler(Exception, system_exception_handler)  # type: ignore


app = APIFactory().create_app()


if __name__ == "__main__":
    """Convenience entrypoint to start the API via APIFactory.run"""
    APIFactory().run()
