"""Base class for ``arrangement.*`` feature kinds."""

from dataclasses import dataclass

from sparc_agi.features.base import Feature


@dataclass
class Arrangement(Feature):
    """Placement plan for object copies. Instantiation yields placement slots."""
