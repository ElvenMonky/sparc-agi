from dataclasses import dataclass

from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature

@register_feature("mapping")
@dataclass
class MappingSpec(FeatureSpec):
    key: str
    variants: Range[1, MAX_COUNT] | None = field(default=None)
    value: Range

@register_feature("mapping.color")
@dataclass
class ColorMappingSpec(MappingSpec):
    pass
