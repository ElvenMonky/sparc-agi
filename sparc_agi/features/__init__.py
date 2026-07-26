"""Auto-import feature modules so ``@register_feature`` runs at import time."""

import importlib
import pkgutil
from pathlib import Path

from sparc_agi.features.base import (
    FEATURE_REGISTRY,
    Feature,
    Sequence,
    feature_family,
    register_feature,
)
from sparc_agi.features.footprint import Footprint
from sparc_agi.features.range import Range
from sparc_agi.features.size import Size

for _, module_name, _ in pkgutil.iter_modules([str(Path(__file__).resolve().parent)]):
    if module_name != "base":
        importlib.import_module(f"{__name__}.{module_name}")

__all__ = [
    "FEATURE_REGISTRY",
    "Feature",
    "Footprint",
    "Range",
    "Sequence",
    "Size",
    "feature_family",
    "register_feature",
]
