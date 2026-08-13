import random
from dataclasses import dataclass, field

from sparc_agi.puzzle.features.base import Filter
from sparc_agi.puzzle.puzzle import Puzzle
from sparc_agi.puzzle_spec.features.base import Access, FeatureSpec, register_feature
from sparc_agi.puzzle_spec.features.object import ObjectSpec, PoolItemSpec
from sparc_agi.puzzle_spec.range import Range

@register_feature("filter")
@dataclass
class FilterSpec(FeatureSpec):
    index: list[int] = field(default_factory=list)
    criteria: list[str] = field(default_factory=list)

    def apply(self, root: ObjectSpec) -> PoolItemSpec:
        current = PoolItemSpec(value=root, variants=Range(1))
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
        if current.value is None:
            raise ValueError("filter resolves to removed pool item")
        return current

    def target(self, root: ObjectSpec) -> ObjectSpec:
        return self.apply(root).value

    def instantiate(self, rng: random.Random) -> Filter:
        del rng
        return Filter(spec=self)

    def refer_target(self, ctx: Puzzle, root: ObjectSpec) -> str:
        slot = self.apply(root)
        parts: list[str] = []
        for name in self.criteria:
            if name == "kind":
                continue
            trait = slot.value.get_trait(name)
            if trait is not None and (phrase := trait.describe(ctx)):
                parts.append(phrase)
        variants = slot.variants or Range(2)
        count = variants.lo if variants.is_fixed() else variants.hi
        parts.append(slot.value.kind_noun(count))
        return f"{' '.join(parts)} from {root.refer(ctx)}"

def filtered_target(
    root: ObjectSpec,
    filter: FilterSpec,
    access: Access,
    trait: str,
) -> ObjectSpec:
    target = filter.target(root)
    if not type(target).has_trait_access(trait, access):
        need = "gettable" if access & Access.GET else "settable"
        if access == Access.RW:
            need = "gettable/settable"
        raise ValueError(
            f"filtered {type(target).tag()} lacks {need} trait {trait!r}"
        )
    return target
