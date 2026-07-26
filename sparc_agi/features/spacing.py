import random
from dataclasses import dataclass, field

from sparc_agi.features.base import Feature, register_feature
from sparc_agi.features.range import Range


@register_feature("spacing")
@dataclass
class Spacing(Feature):
    margin: Range = field(default_factory=lambda: Range(0))
    gap: Range = field(default_factory=lambda: Range(0))

    def describe(self) -> str:
        parts: list[str] = []
        if not self.is_default("margin"):
            parts.append(f"margin {self.margin.describe()}")
        if not self.is_default("gap"):
            parts.append(f"gap {self.gap.describe()}")
        if not parts:
            return ""
        return f"spacing ({', '.join(parts)})"

    def instantiate(self, rng: random.Random) -> tuple[int, int]:
        return (self.margin.sample(rng), self.gap.sample(rng))

