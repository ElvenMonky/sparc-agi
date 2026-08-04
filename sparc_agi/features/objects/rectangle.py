from dataclasses import dataclass

from sparc_agi.features.base import register_feature
from sparc_agi.features.cut import Cut
from sparc_agi.features.objects.base import ObjectSpec
from sparc_agi.features.scalars.color import ColorSpec
from sparc_agi.features.scalars.size import Size

@register_feature("object.rectangle")
@dataclass
class RectangleSpec(ObjectSpec):
    size: Size | None = None
    color: ColorSpec | None = None
    edge_color: ColorSpec | None = None
    cut: Cut | None = None
