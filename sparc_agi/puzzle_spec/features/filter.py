from dataclasses import dataclass, field

from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature
from sparc_agi.puzzle_spec.features.object import PoolItemSpec

@register_feature("filter")
@dataclass
class FilterSpec(FeatureSpec):
    index: list[int] = field(default_factory=list)
    criteria: list[str] = field(default_factory=list)

    def apply(self, slot: PoolItemSpec) -> PoolItemSpec:
        current = slot
        for idx in self.index:
            parent = current.value
            if parent is None:
                raise ValueError(f"filter index {idx} resolves to removed pool item")
            pool = getattr(parent, "pool", None)
            if not pool:
                raise ValueError(
                    f"filter index {idx} but {type(parent).tag()} has no pool"
                )
            if idx < 0 or idx >= len(pool):
                raise ValueError(
                    f"filter index {idx} out of range for {type(parent).tag()} "
                    f"pool of size {len(pool)}"
                )
            current = pool[idx]
        return current
