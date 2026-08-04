from dataclasses import dataclass

from sparc_agi.features.base import register_feature
from sparc_agi.features.objects.base import ObjectSpec
from sparc_agi.features.scalars.color import ColorSpec

@register_feature("object.point")
@dataclass
class PointSpec(ObjectSpec):
    color: ColorSpec | None = None
