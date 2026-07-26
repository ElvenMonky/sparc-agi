"""Point object: a single colored cell."""

import random
from dataclasses import dataclass, field

from sparc_agi.features.base import register_feature
from sparc_agi.features.color import Color
from sparc_agi.features.objects.base import Object
from sparc_agi.features.range import Range


@register_feature("object.point")
@dataclass
class Point(Object):
    color: Color = field(default_factory=lambda: Color(value=Range(0, 10)))

    def describe(self) -> str:
        if self.source is not None and getattr(self.source, "alias", None):
            base = self.source.alias
        else:
            base = "point"
        if self.is_default("color"):
            return base
        return f"{self.color.describe()} {base}"

    def instantiate(self, rng: random.Random) -> list[list[int]]:
        return [[self.color.instantiate(rng)]]
