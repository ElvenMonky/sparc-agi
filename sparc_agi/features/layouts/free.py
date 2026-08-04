from dataclasses import dataclass

from sparc_agi.features.base import register_feature
from sparc_agi.features.layouts.base import LayoutSpec

@register_feature("layout.free")
@dataclass
class FreeLayoutSpec(LayoutSpec):
    pass
