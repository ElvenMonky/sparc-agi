"""Tree object: colored points grown as an 8-connected cluster."""

import random
from dataclasses import dataclass, field

from sparc_agi.geometry import Geometry, point_geometry
from sparc_agi.features.arrangements.tree import TreeArrangement, grow_tree_cells
from sparc_agi.features.base import Feature, register_feature
from sparc_agi.features.objects.base import Object
from sparc_agi.features.scalars.color import Color
from sparc_agi.features.scalars.count import Count
from sparc_agi.range import RangeSpec
from sparc_agi.features.scalars.size import Size
from sparc_agi.features.sequence import Sequence

@register_feature("object.tree")
@dataclass
class Tree(Object):
    """Connected cluster of points (internal tree growth is not a trait).

    Traits: ``color``, optional ``size`` (growth bounds), ``count`` (cells).
    When ``size`` is omitted, growth is unbounded and the result is cropped to
    a tight bbox — so size never appears in descriptions.
    """

    color: Color = field(default_factory=lambda: Color(value=RangeSpec(1, 9)))
    size: Size | None = None
    count: Count = field(default_factory=lambda: Count(value=RangeSpec(15, 30)))

    def kind_noun(self) -> str:
        return "tree structure"

    def describe(self) -> str:
        if isinstance(self.source, Feature) and getattr(self.source, "alias", None):
            base = self.source.alias
        else:
            base = self.kind_noun()
        if self.is_default("color"):
            return base
        return f"{self.color.describe()} {base}"

    def instantiate(self, rng: random.Random) -> Geometry:
        color = self.color.instantiate(rng)
        if self.cache_source_keys():
            return self.instantiate_from_source(rng, color=color)

        if self.size is not None:
            arrangement = TreeArrangement(
                size=self.size,
                sequence=Sequence(cycle=[0]),
                count=self.count,
            )
            width, height = arrangement.size.instantiate(rng)
            placements = arrangement.instantiate(rng)
            children = [
                point_geometry(color, x=x, y=y)
                for (x, y), _ in placements
                if 0 <= x < width and 0 <= y < height
            ]
            return Geometry(width=width, height=height, color=color, geometries=children)

        target = max(1, self.count.instantiate(rng))
        cells = grow_tree_cells(rng, target)
        children = [point_geometry(color, x=x, y=y) for x, y in cells]
        return Geometry(color=color, geometries=children).crop_to_content()
