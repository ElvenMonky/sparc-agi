from dataclasses import dataclass

from sparc_agi.features.base import register_feature
from sparc_agi.features.origin import Origin
from sparc_agi.features.patterns.base import PatternSpec

@register_feature("pattern.radial")
@dataclass
class RadialPatternSpec(PatternSpec):
    origin: Origin | None = None
