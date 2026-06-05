import importlib
import inspect
import os
import pkgutil
import sys
from typing import get_args, get_origin, TypeVar

def discover_command_handlers() -> dict[type, type]:
    """Scan the project's packages and return command/query handlers registry."""
    _scan_packages()
    from src.building_blocks.application.mediator.messages.commands import (
        BaseCommandHandler,
    )
    from src.building_blocks.application.mediator.messages.queries import (
        BaseQueryHandler,
    )

    registry: dict[type, type] = {}

    for base_cls in (BaseCommandHandler, BaseQueryHandler):
        for handler_cls in _all_subclasses(base_cls):
            if inspect.isabstract(handler_cls):
                continue
            request_type = _extract_first_generic_arg(
                handler_cls, (BaseCommandHandler, BaseQueryHandler)
            )
            if request_type is not None:
                registry[request_type] = handler_cls
    return registry


def _scan_packages() -> None:
    """
    Walk every top-level package under sys.path[0] (the project root),
    recursively import all sub-modules so that handler subclasses are
    registered in Python's class hierarchy and can be found via __subclasses__().
    """
    search_path = sys.path[0] or os.getcwd()
    path = os.path.abspath(search_path)

    if path not in sys.path:
        sys.path.insert(0, path)

    ignore_dirs = {".git", ".venv", "venv", "__pycache__", "tests"}

    if not os.path.isdir(path):
        return

    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if not os.path.isdir(item_path) or item in ignore_dirs:
            continue
        try:
            package = importlib.import_module(item)
            pkg_path = getattr(package, "__path__", None)
            if pkg_path:
                for _, module_name, _ in pkgutil.walk_packages(
                    pkg_path, package.__name__ + "."
                ):
                    try:
                        importlib.import_module(module_name)
                    except Exception:
                        pass
        except Exception:
            pass


def _all_subclasses(cls: type) -> list[type]:
    """Recursively collect all (indirect) subclasses of cls."""
    result: list[type] = []
    for sub in cls.__subclasses__():
        result.append(sub)
        result.extend(_all_subclasses(sub))
    return result


def _extract_first_generic_arg(
    handler_cls: type,
    base_classes: tuple[type, ...],
) -> type | None:
    """
    Inspect handler_cls's MRO to find the first concrete type argument
    bound to any of base_classes.
    """
    for cls in handler_cls.__mro__:
        for base in getattr(cls, "__orig_bases__", []):
            origin = get_origin(base) or base
            if isinstance(origin, type) and issubclass(origin, base_classes):
                args = get_args(base)
                if args:
                    candidate = args[0]
                    if not isinstance(candidate, TypeVar):
                        return candidate
    return None
