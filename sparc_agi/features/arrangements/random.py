"""Random arrangement: shuffle footprint cells, then apply sequence / count."""

import random
from dataclasses import dataclass

from sparc_agi.features.arrangements.base import Arrangement
from sparc_agi.features.base import register_feature
from sparc_agi.features.count import Count
from sparc_agi.features.sequence import Sequence
from sparc_agi.features.size import Size


@register_feature("arrangement.random")
@dataclass
class RandomArrangement(Arrangement):
    """Rectangular footprint with cells ordered randomly, then sequence + count.

    Unlike ``arrangement.grid``, there is no scan orientation — coordinates are
    shuffled, so a ``count`` prefix selects a random occupied subset.
    Instantiation yields ``[((x, y), pool_index), ...]``.
    """

    size: Size
    sequence: Sequence
    count: Count | None = None  # omit → fill as many slots as the footprint allows

    def describe(self) -> str:
        text = f"a {self.size.describe()} random arrangement using {self.sequence.describe()}"
        if self.count is not None:
            text += f", {self.count.describe()}"
        return text

    def instantiate(self, rng: random.Random) -> list[tuple[tuple[int, int], int]]:
        width, height = self.size.instantiate(rng)
        coords = [(x, y) for y in range(height) for x in range(width)]
        rng.shuffle(coords)
        self.sequence.instantiate(rng)
        n = len(coords)
        out: list[tuple[tuple[int, int], int]] = []
        for i, coord in enumerate(coords):
            idx = self.sequence.index_at(i, n)
            if idx == -1:
                continue
            out.append((coord, idx))
        if self.count is not None:
            out = out[: self.count.instantiate(rng)]
        return out
