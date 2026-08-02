"""Point object: a single colored cell."""

import random
from dataclasses import dataclass, field

from sparc_agi.geometry import Geometry, point_geometry
from sparc_agi.features.base import Feature, register_feature
from sparc_agi.features.scalars.color import Color
from sparc_agi.features.objects.base import Object
from sparc_agi.range import RangeSpec

@register_feature("object.point")
@dataclass
class Point(Object):
    color: Color = field(default_factory=lambda: Color(value=RangeSpec(0, 9)))

    def describe(self) -> str:
        if isinstance(self.source, Feature) and getattr(self.source, "alias", None):
            base = self.source.alias
        else:
            base = "point"
        if self.is_default("color"):
            return base
        return f"{self.color.describe()} {base}"

    def instantiate(self, rng: random.Random) -> Geometry:
        return point_geometry(self.color.instantiate(rng))
