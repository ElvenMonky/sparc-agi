from dataclasses import dataclass

from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature, trait
from sparc_agi.puzzle_spec.features.scalar import HeightSpec, WidthSpec

@register_feature("size")
@dataclass
class SizeSpec(FeatureSpec):
    width: WidthSpec | None = trait(default=None)
    height: HeightSpec | None = trait(default=None)

@register_feature("layout")
@dataclass
class LayoutSpec(FeatureSpec):
    size: SizeSpec | None = trait(default=None)
