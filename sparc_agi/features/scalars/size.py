import random
from dataclasses import dataclass

from sparc_agi.features.scalars.height import HeightSpec
from sparc_agi.features.scalars.width import WidthSpec
from sparc_agi.range import Range

@dataclass
class Size:
    width: WidthSpec
    height: HeightSpec
    ratio: Range | None = None

    def describe(self) -> str:
        w, h = self.width.value, self.height.value
        if w.lo == w.hi and h.lo == h.hi and w.step == h.step == 1:
            return f"{w.lo}x{h.lo}"
        return f"{self.width.describe()} × {self.height.describe()}"

    def instantiate(self, rng: random.Random) -> tuple[int, int]:
        return (self.width.instantiate(rng), self.height.instantiate(rng))
