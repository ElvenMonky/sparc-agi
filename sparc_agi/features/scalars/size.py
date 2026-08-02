import random
from dataclasses import dataclass

from sparc_agi.features.scalars.height import Height
from sparc_agi.features.scalars.width import Width

@dataclass
class Size:
    width: Width
    height: Height

    def describe(self) -> str:
        w, h = self.width.value, self.height.value
        if w.lo == w.hi and h.lo == h.hi and w.step == h.step == 1:
            return f"{w.lo}x{h.lo}"
        return f"{self.width.describe()} × {self.height.describe()}"

    def instantiate(self, rng: random.Random) -> tuple[int, int]:
        return (self.width.instantiate(rng), self.height.instantiate(rng))
