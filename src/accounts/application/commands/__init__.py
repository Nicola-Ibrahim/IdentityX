import importlib
import pkgutil

# Automatically import all submodules in this package to trigger handler decorators
for _, module_name, _ in pkgutil.walk_packages(__path__, __name__ + "."):
    importlib.import_module(module_name)
