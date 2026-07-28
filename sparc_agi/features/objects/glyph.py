"""Glyph object: sparse colored points on a fixed read-only arrangement."""

import random
from dataclasses import dataclass, field

from sparc_agi.canvas import Geometry, point_geometry
from sparc_agi.features.arrangements.base import Arrangement
from sparc_agi.features.arrangements.random import RandomArrangement
from sparc_agi.features.base import Feature, register_feature
from sparc_agi.features.scalars.color import Color
from sparc_agi.features.scalars.count import Count
from sparc_agi.features.scalars.height import Height
from sparc_agi.features.objects.base import Object
from sparc_agi.features.scalars.range import Range
from sparc_agi.features.sequence import Sequence
from sparc_agi.features.scalars.size import Size
from sparc_agi.features.scalars.width import Width


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

    Traits: ``color``. Optional ``source`` (on :class:`Feature`) inherits from
    any preceding stage (cache keys or a parent feature). ``arrangement`` is
    read-only structure (not a trait).
    """

    __non_traits__ = frozenset({"arrangement"})

    color: Color = field(default_factory=lambda: Color(value=Range(1, 9)))
    arrangement: Arrangement = field(default_factory=_default_glyph_arrangement)

    def describe(self) -> str:
        if isinstance(self.source, Feature) and getattr(self.source, "alias", None):
            base = self.source.alias
        else:
            base = "glyph"
        if self.is_default("color"):
            return base
        return f"{self.color.describe()} {base}"

    def instantiate(self, rng: random.Random) -> Geometry:
        color = self.color.instantiate(rng)
        if self.cache_source_keys():
            return self.instantiate_from_source(rng, color=color)

        size = getattr(self.arrangement, "size", None)
        if size is None:
            raise TypeError(f"{type(self.arrangement).__name__} has no size for glyph")
        width, height = size.instantiate(rng)
        placements = self.arrangement.instantiate(rng)
        children = [
            point_geometry(color, x=x, y=y)
            for (x, y), _ in placements
            if 0 <= x < width and 0 <= y < height
        ]
        return Geometry(width=width, height=height, color=color, geometries=children)
