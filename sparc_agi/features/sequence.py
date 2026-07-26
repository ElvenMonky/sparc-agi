"""Sequence feature: prefix / cycle / suffix pool-index lists."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from sparc_agi.features.base import Feature, register_feature


@register_feature("sequence")
@dataclass
class Sequence(Feature):
    """Pool-index pattern for arrangement slots.

    Instantiation returns ``(prefix, cycle, suffix)``. Index ``-1`` means the
    corresponding footprint slot is left empty (omitted from the result).
    """

    cycle: list[int] = field(default_factory=list)
    prefix: list[int] = field(default_factory=list)
    suffix: list[int] = field(default_factory=list)

    def describe(self) -> str:
        return f"{self.cycle} pattern"

    def instantiate(self, rng: random.Random) -> tuple[list[int], list[int], list[int]]:
        del rng  # deterministic
        return (list(self.prefix), list(self.cycle), list(self.suffix))

    def index_at(self, i: int, n: int) -> int:
        """Pool index for slot ``i`` of ``n`` (prefix, then cycle, then suffix)."""
        if i < len(self.prefix):
            return self.prefix[i]
        suffix_start = n - len(self.suffix)
        if i >= suffix_start and self.suffix:
            return self.suffix[i - suffix_start]
        if not self.cycle:
            return -1
        return self.cycle[(i - len(self.prefix)) % len(self.cycle)]
