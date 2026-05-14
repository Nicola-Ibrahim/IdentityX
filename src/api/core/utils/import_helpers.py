import importlib
import pkgutil
from inspect import getmembers
from typing import Any, Generator, Type, TypeVar

# Define a generic type variable for the member
T = TypeVar("T")


def import_modules_from_package(package_name: str, recursive: bool = False) -> Generator[Any, None, None]:
    """
    Import all modules within the specified package.

    Args:
        package_name (str): The dot-separated package path (e.g., 'src.api.v1.endpoints').
        recursive (bool): If True, import modules from subpackages recursively.

    Yields:
        Iterable[Any]: An iterable of imported modules.
    """
    package = importlib.import_module(package_name)
    package_path = getattr(package, "__path__", [])

    for _, module_name, is_pkg in pkgutil.iter_modules(package_path):
        full_module_name = f"{package_name}.{module_name}"
        module = importlib.import_module(full_module_name)
        yield module
        
        if recursive and is_pkg:
            yield from import_modules_from_package(full_module_name, recursive=True)


def extract_members_from_module(
    module: Any, member_type: Type[T] | None = None, member_name: str | None = None
) -> Generator[T, None, None]:
    """
    Retrieves members from a given module based on type or name.
    """
    for name, member in getmembers(module):
        if (member_type is not None and isinstance(member, member_type)) or (
            member_name is not None and name == member_name
        ):
            yield member


def extract_members_from_package(
    package_name: str, 
    member_type: Type[T] | None = None, 
    member_name: str | None = None,
    recursive: bool = False
) -> Generator[T, None, None]:
    """
    Imports all modules from a package and retrieves specified members from them.
    """
    modules = import_modules_from_package(package_name, recursive=recursive)

    for module in modules:
        yield from extract_members_from_module(module, member_type, member_name)
