import random
from dataclasses import dataclass, field

from sparc_agi.features.base import FeatureSpec, register_feature

@register_feature("pattern")
@dataclass
class PatternSpec(FeatureSpec):
    prefix: list[int] = field(default_factory=list)
    pattern: list[int] = field(default_factory=list)
    suffix: list[int] = field(default_factory=list)

    def index_at(
        self,
        index: int,
        count: int,
        pool_size: int,
        rng: random.Random,
    ) -> int:
        if index < len(self.prefix):
            return self.prefix[index]
        suffix_start = count - len(self.suffix)
        if index >= suffix_start and self.suffix:
            return self.suffix[index - suffix_start]
        if not self.pattern:
            if pool_size < 1:
                raise ValueError("random pattern requires a non-empty pool")
            return rng.randrange(pool_size)
        return self.pattern[(index - len(self.prefix)) % len(self.pattern)]
