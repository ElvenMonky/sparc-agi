"""Footprint features: coordinate sets an arrangement can occupy."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from sparc_agi.features.base import Feature, register_feature
from sparc_agi.features.orientation import Orientation, scan_cells
from sparc_agi.features.range import Range
from sparc_agi.features.size import Size


@register_feature("footprint.grid")
@dataclass
class GridFootprint(Feature):
    """Rectangular grid of cells, ordered by orientation scan."""

    size: Size
    orientation: Orientation = field(default_factory=lambda: Orientation(value=Range(0)))

    def describe(self) -> str:
        text = f"{self.size.describe()} grid footprint"
        scan = self.orientation.grid_scan_phrase()
        if scan:
            text += f", applied {scan}"
        return text

    def instantiate(self, rng: random.Random) -> list[tuple[int, int]]:
        width, height = self.size.instantiate(rng)
        direction = self.orientation.instantiate(rng)
        return scan_cells(width, height, direction)
