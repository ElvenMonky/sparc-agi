from dataclasses import dataclass

from sparc_agi.features.base import register_feature
from sparc_agi.features.scalars.base import ScalarSpec

@register_feature("height")
@dataclass
class Height(ScalarSpec):
    pass
