from dataclasses import dataclass, field

from sparc_agi.features.base import register_feature
from sparc_agi.features.layouts.base import LayoutSpec
from sparc_agi.features.objects.base import ObjectSpec, PoolItem
from sparc_agi.features.patterns.base import PatternSpec
from sparc_agi.features.scalars.count import CountSpec
from sparc_agi.features.scalars.size import Size
from sparc_agi.features.spacing import SpacingSpec

@register_feature("object.group")
@dataclass
class GroupSpec(ObjectSpec):
    size: Size | None = None
    count: CountSpec | None = None
    spacing: SpacingSpec | None = None
    layout: LayoutSpec | None = None
    pattern: PatternSpec | None = None
    pool: list[PoolItem] = field(default_factory=list)
