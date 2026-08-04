"""Scalar features (``color``, ``count``, ``width``, …) and helpers (``Range``, ``Size``).

Call :func:`load_scalar_features` from :mod:`sparc_agi.features` after ``base``
is imported so ``Range`` can load without a circular import.
"""

import importlib

from sparc_agi.features.scalars.base import Scalar, ScalarSpec
from sparc_agi.range import Range

__all__ = ["Range", "Scalar", "ScalarSpec", "load_scalar_features"]

def load_scalar_features() -> None:
    """Import scalar modules so ``@register_feature`` / ``Size`` are available."""
    for module_name in ("color", "count", "height", "orientation", "size", "width"):
        importlib.import_module(f"{__name__}.{module_name}")
