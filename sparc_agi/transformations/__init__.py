"""Auto-import transformation modules so ``@register_transformation`` runs at import time."""

import importlib
import pkgutil
from pathlib import Path

from sparc_agi.transformations.base import (
    TRANSFORMATION_REGISTRY,
    Transformation,
    WireRef,
    register_transformation,
)

for _, module_name, _ in pkgutil.iter_modules([str(Path(__file__).resolve().parent)]):
    if module_name != "base":
        importlib.import_module(f"{__name__}.{module_name}")

__all__ = [
    "TRANSFORMATION_REGISTRY",
    "Transformation",
    "WireRef",
    "register_transformation",
]
