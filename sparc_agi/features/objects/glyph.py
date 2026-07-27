"""Glyph object: sparse colored points on a fixed read-only arrangement."""

import random
from dataclasses import dataclass, field

from sparc_agi.features.arrangements.base import Arrangement
from sparc_agi.features.arrangements.random import RandomArrangement
from sparc_agi.features.base import register_feature
from sparc_agi.features.color import Color
from sparc_agi.features.count import Count
from sparc_agi.features.height import Height
from sparc_agi.features.objects.base import Object
from sparc_agi.features.range import Range
from sparc_agi.features.sequence import Sequence
from sparc_agi.features.size import Size
from sparc_agi.features.width import Width


def _default_glyph_arrangement() -> RandomArrangement:
    """Internal 3×3 random arrangement; count prefix yields 2..8 occupied cells."""
    return RandomArrangement(
        size=Size(
            width=Width(value=Range(3)),
            height=Height(value=Range(3)),
        ),
        sequence=Sequence(cycle=[0]),
        count=Count(value=Range(2, 8)),
    )


@register_feature("object.glyph")
@dataclass
class Glyph(Object):
    """Sparse motif on a built-in random arrangement.

    Traits: ``color`` only. ``arrangement`` is read-only structure (not a trait):
    it can be extracted but not rewritten by transforms.
    """

    __non_traits__ = frozenset({"arrangement"})

    color: Color = field(default_factory=lambda: Color(value=Range(1, 9)))
    arrangement: Arrangement = field(default_factory=_default_glyph_arrangement)

    def describe(self) -> str:
        if self.source is not None and getattr(self.source, "alias", None):
            base = self.source.alias
        else:
            base = "glyph"
        if self.is_default("color"):
            return base
        return f"{base}, {self.color.describe()}"

    def instantiate(self, rng: random.Random) -> list[list[int]]:
        size = getattr(self.arrangement, "size", None)
        if size is None:
            raise TypeError(f"{type(self.arrangement).__name__} has no size for glyph paint")
        width, height = size.instantiate(rng)
        placements = self.arrangement.instantiate(rng)
        color = self.color.instantiate(rng)
        grid = [[0] * width for _ in range(height)]
        for (x, y), _ in placements:
            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = color
        return grid
