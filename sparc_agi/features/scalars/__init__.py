"""Scalar features (``color``, ``count``, ``width``, …) and helpers (``Range``, ``Size``).

Call :func:`load_scalar_features` from :mod:`sparc_agi.features` after ``base``
is imported so ``Range`` can load without a circular import.
"""

from sparc_agi.features.scalars.range import Range

__all__ = ["Range", "load_scalar_features"]


def load_scalar_features() -> None:
    """Import scalar modules so ``@register_feature`` / ``Size`` are available."""
    import importlib

    for module_name in ("color", "count", "height", "width", "orientation", "size"):
        importlib.import_module(f"{__name__}.{module_name}")
