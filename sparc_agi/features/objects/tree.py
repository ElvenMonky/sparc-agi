from dataclasses import dataclass, field

from sparc_agi.features.base import register_feature
from sparc_agi.features.objects.base import ObjectSpec, PoolItem
from sparc_agi.features.scalars.color import ColorSpec
from sparc_agi.features.scalars.count import CountSpec
from sparc_agi.features.spacing import SpacingSpec

@register_feature("object.tree_structure")
@dataclass
class TreeStructureSpec(ObjectSpec):
    color: ColorSpec | None = None
    count: CountSpec | None = None
    spacing: SpacingSpec | None = None
    pool: list[PoolItem] = field(default_factory=list)
