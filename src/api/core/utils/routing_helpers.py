from fastapi import APIRouter

from src.api.core.utils.import_helpers import extract_members_from_package

# Packages containing FastAPI routers. ``collect_routers`` will scan
# these packages and import any members that are instances of
# ``APIRouter``.
#
# We now use recursive discovery on the v1 package, so any new
# module or subpackage added under api.routers.v1 will be
# automatically discovered if it contains an APIRouter.
PACKAGE_PATHS = [
    "src.api.routers.v1",
]


def collect_routers(router_type=APIRouter):
    """
    Prepare and return a list of APIRouter instances.

    This function iterates over the PACKAGE_PATHS, imports the routers from each package
    recursively, and combines them into a single list.

    It uses a set to ensure each router instance is only registered once, even if it is
    imported via multiple modules (e.g., in both __init__.py and endpoints.py).

    Returns:
        list: A list of unique APIRouter instances.
    """
    routers = []
    seen_router_ids = set()

    for package_path in PACKAGE_PATHS:
        # We enable recursive=True to find routers in subpackages like .accounts and .admin
        package_routers = extract_members_from_package(package_path, member_type=router_type, recursive=True)

        for router in package_routers:
            router_id = id(router)
            if router_id not in seen_router_ids:
                routers.append(router)
                seen_router_ids.add(router_id)

    return routers
