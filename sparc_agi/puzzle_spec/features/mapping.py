from dataclasses import dataclass, field

from sparc_agi.consts import MAX_COUNT
from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature
from sparc_agi.puzzle_spec.range import Range

@dataclass
class MappingSpec(FeatureSpec):
    key: str
    value: Range
    variants: Range[1, MAX_COUNT] | None = field(default=None)

@register_feature("mapping.color")
@dataclass
class ColorMappingSpec(MappingSpec):
    pass
