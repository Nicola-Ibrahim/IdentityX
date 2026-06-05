import importlib
import inspect
import os
import pkgutil
import sys
from typing import TypeVar, get_args, get_origin


def discover_event_handlers() -> dict[type, list[type]]:
    """Scan the project's packages and return event handlers registry."""
    _scan_packages()
    from src.building_blocks.application.events.base_event_handler import (
        BaseEventHandler,
    )

    registry: dict[type, list[type]] = {}

    for handler_cls in _all_subclasses(BaseEventHandler):
        if inspect.isabstract(handler_cls):
            continue
        event_type = _extract_first_generic_arg(handler_cls, (BaseEventHandler,))
        if event_type is None:
            continue
        if event_type not in registry:
            registry[event_type] = []
        if handler_cls not in registry[event_type]:
            registry[event_type].append(handler_cls)
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
                for _, module_name, _ in pkgutil.walk_packages(pkg_path, package.__name__ + "."):
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
