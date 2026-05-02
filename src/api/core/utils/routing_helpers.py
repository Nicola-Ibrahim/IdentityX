from fastapi import APIRouter

from .import_helpers import extract_members_from_package

# Packages containing FastAPI routers.  ``collect_routers`` will scan
# these packages and import any members that are instances of
# ``APIRouter``.  Each package corresponds to a bounded context and
# versioned API.  Adding a new package here will automatically
# register its routes with the application.
# Define which packages contain API routers.  When the application
# starts it will scan these packages and collect any objects of type
# ``APIRouter`` into a single list for registration.  The user-centric
# routes now live exclusively under ``accounts``.
PACKAGE_PATHS = [
    "src.api.routers.accounts.v1.accounts",
    "src.api.routers.accounts.v1.admin",
    "src.api.routers.accounts.v1.discovery",
]


def collect_routers(router_type=APIRouter):
    """
    Prepare and return a list of APIRouter instances.

    This function iterates over the PACKAGE_PATHS, imports the routers from each package,
    and combines them into a single list.

    Returns:
        list: A list of APIRouter instances.
    """
    routers = []
    for package_path in PACKAGE_PATHS:
        package_routers = extract_members_from_package(package_path, member_type=router_type)
        routers.extend(package_routers)
    return routers
