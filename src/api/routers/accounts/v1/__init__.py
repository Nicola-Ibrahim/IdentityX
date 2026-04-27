"""Version 1 of the accounts API.

This package exposes a single FastAPI ``router`` which aggregates
all version 1 endpoints for the accounts bounded context.  The
``accounts`` submodule defines the routes that make up the
accounts API.  ``collect_routers`` will discover and register
this router along with any others defined in the API module
hierarchy.
"""

from fastapi import APIRouter

from .accounts import router as accounts_router

router = APIRouter()
router.include_router(accounts_router)

__all__ = ["router"]
