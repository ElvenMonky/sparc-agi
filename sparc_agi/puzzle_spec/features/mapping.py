import random
from dataclasses import dataclass, field
from typing import ClassVar

from sparc_agi.consts import MAX_COUNT
from sparc_agi.puzzle.features.base import Mapping
from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature
from sparc_agi.puzzle_spec.range import Range

@dataclass
class MappingSpec(FeatureSpec):
    source_trait: ClassVar[str | None] = None
    target_trait: ClassVar[str | None] = None
    value: Range
    variants: Range[1, MAX_COUNT] | None = field(default=None)

    def instantiate(self, rng: random.Random) -> Mapping:
        del rng
        return Mapping(spec=self, value={})

@register_feature("mapping.arrangement_to_color")
@dataclass
class MaskToColorMappingSpec(MappingSpec):
    source_trait = "arrangement"
    target_trait = "color"

@register_feature("mapping.width_to_color")
@dataclass
class WidthToColorMappingSpec(MappingSpec):
    source_trait = "size.width"
    target_trait = "color"
