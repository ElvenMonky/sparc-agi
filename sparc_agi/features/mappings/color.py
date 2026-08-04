from dataclasses import dataclass

from sparc_agi.features.base import register_feature
from sparc_agi.features.mappings.base import MappingSpec
from sparc_agi.features.scalars.color import ColorSpec

@register_feature("mapping.color")
@dataclass
class ColorMappingSpec(MappingSpec):
    color: ColorSpec | None = None
