"""Grid arrangement: scan a rectangular footprint, then apply a sequence."""

import random
from dataclasses import dataclass, field

from sparc_agi.features.arrangements.base import Arrangement
from sparc_agi.features.base import register_feature
from sparc_agi.features.scalars.orientation import Orientation, transform_xy
from sparc_agi.range import Range

def _scan_phrase(direction: int) -> str | None:
    """How identity row-major fill appears after orientation ``direction``.

    Returns e.g. ``\"column by column from top to bottom and right to left\"``,
    or ``None`` for the default identity scan (omit from descriptions).
    """
    even = direction - (direction % 2)  # silently drop 45°
    if even == 0:
        return None

    n = 3
    pts = GridArrangement.scan_cells(n, n, even)
    dx = pts[1][0] - pts[0][0]
    dy = pts[1][1] - pts[0][1]
    if dx != 0 and dy == 0:
        major = "row by row"
        along = "left to right" if dx > 0 else "right to left"
        across = "top to bottom" if pts[n][1] > pts[0][1] else "bottom to top"
    elif dy != 0 and dx == 0:
        major = "column by column"
        along = "top to bottom" if dy > 0 else "bottom to top"
        across = "left to right" if pts[n][0] > pts[0][0] else "right to left"
    else:
        return f"orientation {even}"

    return f"{major} from {along} and {across}"

@register_feature("arrangement.grid")
@dataclass
class GridArrangement(Arrangement):
    """Rectangular arrangement: scan a size×orientation grid, then apply sequence.

    Instantiation yields ``[((x, y), pool_index), ...]`` with empty (``-1``)
    sequence slots removed. ``count`` (when set) keeps a prefix of those slots.
    """

    orientation: Orientation = field(default_factory=lambda: Orientation(value=Range(0)))

    @staticmethod
    def scan_cells(width: int, height: int, direction: int) -> list[tuple[int, int]]:
        """Cell coordinates in fill order for a ``width``×``height`` grid.

        Identity fill is row-major; ``direction``'s even dihedral half
        reorders/positions cells. The +45° bit is dropped by design for grids.
        """
        pts = [transform_xy(x, y, direction) for y in range(height) for x in range(width)]
        min_x = min(p[0] for p in pts)
        min_y = min(p[1] for p in pts)
        return [(x - min_x, y - min_y) for x, y in pts]

    def grid_scan_phrase(self) -> str | None:
        """Scan-order phrase for this arrangement, or ``None`` when default."""
        if self.orientation.value.lo != self.orientation.value.hi:
            return f"orientation {self.orientation.value.describe()}"
        return _scan_phrase(self.orientation.value.lo)

    def describe(self) -> str:
        text = f"a {self.size.describe()} grid using {self.sequence.describe()}"
        scan = self.grid_scan_phrase()
        if scan:
            text += f", applied {scan}"
        if self.count is not None:
            text += f", {self.count.describe()}"
        if not self.is_default("spacing"):
            spacing = self.spacing.describe()
            if spacing:
                text += f", {spacing}"
        return text

    def instantiate(self, rng: random.Random) -> list[tuple[tuple[int, int], int]]:
        width, height = self.size.instantiate(rng)
        direction = self.orientation.instantiate(rng)
        coords = self.scan_cells(width, height, direction)
        self.sequence.instantiate(rng)
        n = len(coords)
        out: list[tuple[tuple[int, int], int]] = []
        for i, coord in enumerate(coords):
            idx = self.sequence.index_at(i, n)
            if idx == -1:
                continue
            out.append((coord, idx))
        if self.count is not None:
            out = out[: self.count.instantiate(rng)]
        return out
