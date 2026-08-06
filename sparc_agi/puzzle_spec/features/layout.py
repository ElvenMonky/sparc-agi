from dataclasses import dataclass

from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature
from sparc_agi.puzzle_spec.features.scalar import HeightSpec, WidthSpec

@register_feature("size")
@dataclass
class SizeSpec(FeatureSpec):
    width: WidthSpec | None = None
    height: HeightSpec | None = None

@register_feature("layout")
@dataclass
class LayoutSpec(FeatureSpec):
    size: SizeSpec | None = None
