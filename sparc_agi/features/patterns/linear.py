from dataclasses import dataclass

from sparc_agi.features.base import register_feature
from sparc_agi.features.patterns.base import PatternSpec
from sparc_agi.features.scalars.orientation import OrientationSpec

@register_feature("pattern.linear")
@dataclass
class LinearPatternSpec(PatternSpec):
    orientation: OrientationSpec | None = None
