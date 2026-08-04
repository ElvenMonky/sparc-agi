from dataclasses import dataclass

from sparc_agi.features.base import FeatureSpec
from sparc_agi.features.patterns.base import PatternSpec
from sparc_agi.features.scalars.size import Size
from sparc_agi.features.spacing import SpacingSpec

@dataclass
class LayoutSpec(FeatureSpec):
    size: Size | None = None
    pattern: PatternSpec | None = None
    spacing: SpacingSpec | None = None
