"""Base class for ``object.*`` feature kinds."""

from dataclasses import dataclass

from sparc_agi.features.base import Feature


@dataclass
class Object(Feature):
    """Renderable object. Instantiation yields an ARC color grid (``-1`` = transparent)."""
