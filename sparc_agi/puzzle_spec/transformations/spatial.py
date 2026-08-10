from copy import deepcopy
from dataclasses import dataclass

from sparc_agi.puzzle_spec.features.arrangement import ArrangementSlotSpec, ArrangementSpec
from sparc_agi.puzzle_spec.features.base import FeatureSpec, FilterSpec
from sparc_agi.puzzle_spec.features.object import BaseGroupSpec, GridSpec, ObjectSpec, PoolItemSpec
from sparc_agi.puzzle_spec.features.pattern import PatternSlotSpec, PatternSpec
from sparc_agi.puzzle_spec.filter import filter_ref
from sparc_agi.puzzle_spec.transformations.base import TransformationSpec, register_transformation
from sparc_agi.puzzle_spec.wire import WireRef

@dataclass
class SpatialSpec[Object: FeatureSpec](TransformationSpec[Object]):
    object: WireRef[Object]

    @classmethod
    def trace(cls, object: Object) -> Object:
        return deepcopy(object)

@register_transformation("RemoveObjects")
@dataclass
class RemoveObjectsSpec(SpatialSpec[BaseGroupSpec]):
    filter: WireRef[FilterSpec] = filter_ref()

    @classmethod
    def trace(cls, object: BaseGroupSpec, filter: FilterSpec) -> BaseGroupSpec:
        return deepcopy(object)

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
