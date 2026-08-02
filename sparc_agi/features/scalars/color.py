from dataclasses import dataclass

from sparc_agi.features.base import register_feature
from sparc_agi.features.scalars.base import ScalarSpec

@register_feature("color")
@dataclass
class ColorSpec(ScalarSpec):
    def describe(self) -> str:
        return ", ".join(str(v) for v in range(self.value.lo, self.value.hi + 1, self.value.step))
