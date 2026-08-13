import random
from dataclasses import dataclass, field

from sparc_agi.puzzle.features.base import Filter
from sparc_agi.puzzle.puzzle import Puzzle
from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature
from sparc_agi.puzzle_spec.features.object import ObjectSpec, PoolItemSpec
from sparc_agi.puzzle_spec.range import Range

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

    def target(self, root: ObjectSpec) -> ObjectSpec | None:
        return self.apply(PoolItemSpec(value=root)).value

    def target_count(self, root: ObjectSpec) -> Range | int | None:
        variants = self.apply(PoolItemSpec(value=root, variants=1)).variants
        if variants is not None and variants.is_fixed() and variants.lo == 1:
            return 1
        if variants is not None:
            return variants
        return 2

    def instantiate(self, rng: random.Random) -> Filter:
        del rng
        return Filter(spec=self)

    def refer_target(self, ctx: Puzzle, root: ObjectSpec) -> str:
        obj = self.target(root)
        if obj is None:
            raise ValueError("filter resolves to removed pool item")
        parts: list[str] = []
        for name in self.criteria:
            if name == "kind":
                continue
            trait = obj.get_trait(name)
            if trait is not None and (phrase := trait.describe(ctx)):
                parts.append(phrase)
        parts.append(obj.kind_noun(self.target_count(root)))
        return f"{' '.join(parts)} from {root.refer(ctx)}"
