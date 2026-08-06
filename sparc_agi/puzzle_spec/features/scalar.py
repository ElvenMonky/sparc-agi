import random
from dataclasses import dataclass, field

from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature
from sparc_agi.puzzle_spec.range import Range
from sparc_agi.consts import MAX_COLOR, MAX_SIZE

@dataclass
class ScalarSpec(FeatureSpec):
    value: Range = field(default_factory=Range)

    def unstructure(self) -> int | list[int]:
        return self.value.unstructure()

    def instantiate(self, rng: random.Random) -> int:
        return self.value.instantiate(rng)

@register_feature("color")
@dataclass
class ColorSpec(ScalarSpec):
    value: Range[0, MAX_COLOR] = field(default_factory=Range)

@register_feature("width")
@dataclass
class WidthSpec(ScalarSpec):
    value: Range[1, MAX_SIZE] = field(default_factory=Range)

@register_feature("height")
@dataclass
class HeightSpec(ScalarSpec):
    value: Range[1, MAX_SIZE] = field(default_factory=Range)
