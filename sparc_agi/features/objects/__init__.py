"""Auto-import object kind modules so ``@register_feature`` runs at import time."""

import importlib
import pkgutil
from pathlib import Path

from sparc_agi.features.objects.base import Object

for _, module_name, _ in pkgutil.iter_modules([str(Path(__file__).resolve().parent)]):
    if module_name != "base":
        importlib.import_module(f"{__name__}.{module_name}")

__all__ = ["Object"]
