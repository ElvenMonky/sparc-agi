"""Glyph object: sparse colored points on a fixed read-only arrangement."""

import random
from dataclasses import dataclass, field

from sparc_agi.geometry import Geometry, point_geometry
from sparc_agi.features.arrangements.base import Arrangement
from sparc_agi.features.arrangements.random import RandomArrangement
from sparc_agi.features.base import Feature, register_feature
from sparc_agi.features.scalars.color import Color
from sparc_agi.features.scalars.count import Count
from sparc_agi.features.scalars.height import Height
from sparc_agi.features.objects.base import Object
from sparc_agi.range import RangeSpec
from sparc_agi.features.sequence import Sequence
from sparc_agi.features.scalars.size import Size
from sparc_agi.features.scalars.width import Width

@register_feature("object.glyph")
@dataclass
class Glyph(Object):
    """Sparse motif on a built-in random arrangement.

    Traits: ``color``. Optional ``source`` (on :class:`Feature`) inherits from
    any preceding stage (cache keys or a parent feature). ``arrangement`` is
    read-only structure (not a trait).
    """

    color: Color = field(default_factory=lambda: Color(value=RangeSpec(1, 9)))
    default_arrangement = RandomArrangement(
        size=Size(
            width=Width(value=RangeSpec(3)),
            height=Height(value=RangeSpec(3)),
        ),
        sequence=Sequence(cycle=[0]),
        count=Count(value=RangeSpec(2, 8)),
    )

    def describe(self) -> str:
        base = "glyph"
        if isinstance(self.source, Feature) and getattr(self.source, "alias", None):
            base = self.source.alias
            
        if self.is_default("color"):
            return base
        return f"{self.color.describe()} {base}"

    def instantiate(self, rng: random.Random) -> Geometry:
        color = self.color.instantiate(rng)
        if self.cache_source_keys():
            return self.instantiate_from_source(rng, color=color)

        placements = type(self).default_arrangement.instantiate(rng)
        children = [point_geometry(color, x=x, y=y) for (x, y), _ in placements]
        return Geometry(color=color, geometries=children)
