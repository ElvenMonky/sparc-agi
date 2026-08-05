from dataclasses import dataclass

from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature

@register_feature("mapping")
@dataclass
class MappingSpec(FeatureSpec):
    pass

@register_feature("mapping.color")
@dataclass
class ColorMappingSpec(MappingSpec):
    pass