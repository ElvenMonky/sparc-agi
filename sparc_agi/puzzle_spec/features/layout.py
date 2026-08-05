from dataclasses import dataclass

from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature
from sparc_agi.puzzle_spec.range import Range

@register_feature("size")
@dataclass
class SizeSpec(FeatureSpec):
    width: Range | None = None
    height: Range | None = None

@register_feature("layout")
@dataclass
class LayoutSpec(FeatureSpec):
    size: SizeSpec | None = None
