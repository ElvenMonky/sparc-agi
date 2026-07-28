"""Auto-import feature modules so ``@register_feature`` runs at import time."""

import importlib
import pkgutil
from pathlib import Path

from sparc_agi.features.base import (
    FEATURE_REGISTRY,
    Feature,
    Scalar,
    feature_family,
    register_feature,
)
from sparc_agi.features.scalars import load_scalar_features
from sparc_agi.features.scalars.range import Range

load_scalar_features()

from sparc_agi.features.scalars.size import Size  # noqa: E402
from sparc_agi.features.sequence import Sequence  # noqa: E402

for _, module_name, _ in pkgutil.iter_modules([str(Path(__file__).resolve().parent)]):
    if module_name in ("base", "scalars"):
        continue
    importlib.import_module(f"{__name__}.{module_name}")

__all__ = [
    "FEATURE_REGISTRY",
    "Feature",
    "Range",
    "Scalar",
    "Sequence",
    "Size",
    "feature_family",
    "register_feature",
]
