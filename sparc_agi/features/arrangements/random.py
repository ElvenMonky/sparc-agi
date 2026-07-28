"""Random arrangement: shuffle footprint cells, then apply sequence / count."""

import random
from dataclasses import dataclass

from sparc_agi.features.arrangements.base import Arrangement
from sparc_agi.features.base import register_feature


@register_feature("arrangement.random")
@dataclass
class RandomArrangement(Arrangement):
    """Rectangular footprint with cells ordered randomly, then sequence + count.

    Unlike ``arrangement.grid``, there is no scan orientation — coordinates are
    shuffled, so a ``count`` prefix selects a random occupied subset.
    Instantiation yields ``[((x, y), pool_index), ...]``.
    """

    def describe(self) -> str:
        return self.describe_core("random arrangement")

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
