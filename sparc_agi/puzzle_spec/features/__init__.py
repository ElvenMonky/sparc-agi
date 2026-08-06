import importlib
import pkgutil

for module in pkgutil.walk_packages(__path__, prefix=f"{__name__}."):
    importlib.import_module(module.name)
