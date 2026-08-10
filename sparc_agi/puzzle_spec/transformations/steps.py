from dataclasses import dataclass

from sparc_agi.puzzle_spec.features.arrangement import ArrangementSlotSpec, ArrangementSpec
from sparc_agi.puzzle_spec.features.base import Access, FilterSpec
from sparc_agi.puzzle_spec.features.mapping import MaskToColorMappingSpec, WidthToColorMappingSpec
from sparc_agi.puzzle_spec.features.object import BaseGroupSpec, GridSpec, ObjectSpec, PoolItemSpec
from sparc_agi.puzzle_spec.features.pattern import PatternSlotSpec, PatternSpec
from sparc_agi.puzzle_spec.features.scalar import ColorSpec, OrientationSpec
from sparc_agi.puzzle_spec.filter import filter_ref
from sparc_agi.puzzle_spec.transformations.base import TransformationSpec, register_transformation
from sparc_agi.puzzle_spec.wire import WireRef

@register_transformation("Rotate")
@dataclass
class RotateSpec(TransformationSpec[ObjectSpec]):
    orientation: WireRef[OrientationSpec]
    object: WireRef[ObjectSpec]
    filter: WireRef[FilterSpec] = filter_ref((Access.SET, "orientation"), default=None)

    @classmethod
    def trace(
        cls,
        orientation: OrientationSpec,
        object: ObjectSpec,
        filter: FilterSpec | None = None,
    ) -> ObjectSpec:
        return object

@register_transformation("ExtractArrangement")
@dataclass
class ExtractArrangementSpec(TransformationSpec[ArrangementSpec]):
    object: WireRef[ObjectSpec]

    @classmethod
    def trace(cls, object: ObjectSpec) -> ArrangementSpec:
        slot = getattr(object, "arrangement", None)
        if slot is None:
            raise ValueError(f"{type(object).tag()} has no arrangement to extract")
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

@register_transformation("ApplyMaskToColorMapping")
@dataclass
class ApplyMaskToColorMappingSpec(TransformationSpec[ObjectSpec]):
    mapping: WireRef[MaskToColorMappingSpec]
    object: WireRef[ObjectSpec]
    source_filter: WireRef[FilterSpec] = filter_ref((Access.GET, "mask"))
    target_filter: WireRef[FilterSpec] = filter_ref((Access.SET, "color"))

    @classmethod
    def trace(
        cls,
        mapping: MaskToColorMappingSpec,
        object: ObjectSpec,
        source_filter: FilterSpec,
        target_filter: FilterSpec,
    ) -> ObjectSpec:
        return object

@register_transformation("ApplyWidthToColorMapping")
@dataclass
class ApplyWidthToColorMappingSpec(TransformationSpec[ObjectSpec]):
    mapping: WireRef[WidthToColorMappingSpec]
    object: WireRef[ObjectSpec]
    source_filter: WireRef[FilterSpec] = filter_ref((Access.GET, "size.width"))
    target_filter: WireRef[FilterSpec] = filter_ref((Access.SET, "color"))

    @classmethod
    def trace(
        cls,
        mapping: WidthToColorMappingSpec,
        object: ObjectSpec,
        source_filter: FilterSpec,
        target_filter: FilterSpec,
    ) -> ObjectSpec:
        return object

@register_transformation("ChangeColor")
@dataclass
class ChangeColorSpec(TransformationSpec[ObjectSpec]):
    color: WireRef[ColorSpec]
    object: WireRef[ObjectSpec]
    filter: WireRef[FilterSpec] = filter_ref((Access.SET, "color"))

    @classmethod
    def trace(
        cls,
        color: ColorSpec,
        object: ObjectSpec,
        filter: FilterSpec,
    ) -> ObjectSpec:
        return object

@register_transformation("RemoveObjects")
@dataclass
class RemoveObjectsSpec(TransformationSpec[BaseGroupSpec]):
    object: WireRef[BaseGroupSpec]
    filter: WireRef[FilterSpec] = filter_ref()

    @classmethod
    def trace(
        cls,
        object: BaseGroupSpec,
        filter: FilterSpec,
    ) -> BaseGroupSpec:
        return object
