from copy import deepcopy
from dataclasses import dataclass

from sparc_agi.puzzle_spec.features.arrangement import ArrangementSlotSpec, ArrangementSpec
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
