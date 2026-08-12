from copy import deepcopy
from dataclasses import dataclass

from sparc_agi.puzzle.puzzle import Puzzle
from sparc_agi.puzzle_spec.features.arrangement import ArrangementSlotSpec, ArrangementSpec
from sparc_agi.puzzle_spec.features.base import FeatureSpec
from sparc_agi.puzzle_spec.features.filter import FilterSpec
from sparc_agi.puzzle_spec.features.object import BaseGroupSpec, GridSpec, ObjectSpec, PoolItemSpec
from sparc_agi.puzzle_spec.features.pattern import PatternSlotSpec, PatternSpec
from sparc_agi.puzzle_spec.transformations.base import TransformationSpec, register_transformation
from sparc_agi.puzzle_spec.wire import WireRef, filter_ref

@register_transformation("RemoveObjects")
@dataclass
class RemoveObjectsSpec(TransformationSpec[BaseGroupSpec]):
    object: WireRef[BaseGroupSpec]
    filter: WireRef[FilterSpec] = filter_ref()

    @classmethod
    def trace(cls, object: BaseGroupSpec, filter: FilterSpec) -> BaseGroupSpec:
        root = deepcopy(object)
        slot = PoolItemSpec(value=root)
        filter.apply(slot).value = None
        return slot.value

    def describe(self, ctx: Puzzle, *, object: ObjectSpec, filter: FilterSpec) -> str:
        return f"Remove {filter.refer_target(ctx, object)}."

@register_transformation("ArrangeObjects")
@dataclass
class ArrangeObjectsSpec(TransformationSpec[GridSpec]):
    arrangement: WireRef[ArrangementSpec]
    pattern: WireRef[PatternSpec]
    pool: list[WireRef[ObjectSpec]]

    @classmethod
    def trace(
        cls,
        arrangement: ArrangementSpec,
        pattern: PatternSpec | None,
        pool: list[ObjectSpec],
    ) -> GridSpec:
        return GridSpec(
            arrangement=ArrangementSlotSpec(arrangement),
            pattern=PatternSlotSpec(pattern) if pattern is not None else None,
            pool=[PoolItemSpec(value=obj) for obj in pool],
        )

    def alias_stem(
        self,
        *,
        arrangement: ArrangementSpec,
        pattern: PatternSpec | None,
        pool: list[ObjectSpec],
    ) -> str:
        return "arranged "

    def describe(
        self,
        ctx: Puzzle,
        *,
        arrangement: ArrangementSpec,
        pattern: PatternSpec | None,
        pool: list[ObjectSpec],
    ) -> str:
        refs = [obj.refer(ctx) for obj in pool]
        if not refs:
            copies = "no items"
        elif len(refs) == 1:
            copies = f"copies of {refs[0]}"
        elif len(refs) == 2:
            copies = f"copies of {refs[0]} and {refs[1]}"
        else:
            *rest, last = refs
            copies = "copies of " + ", ".join(rest) + f", and {last}"
        place = arrangement.refer(ctx)
        pattern_desc = ""
        if pattern is not None and (desc := pattern.refer(ctx)):
            pattern_desc = f" using {desc}"
        return f"Arrange {copies} into {place}{pattern_desc}."
