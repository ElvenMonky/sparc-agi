from dataclasses import dataclass

from sparc_agi.puzzle_spec.features.arrangement import ArrangementSpec
from sparc_agi.puzzle_spec.features.base import Access, FilterSpec
from sparc_agi.puzzle_spec.features.mapping import MaskToColorMappingSpec, WidthToColorMappingSpec
from sparc_agi.puzzle_spec.features.object import BaseGroupSpec, GridSpec, ObjectSpec
from sparc_agi.puzzle_spec.features.pattern import PatternSpec
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

@register_transformation("ExtractArrangement")
@dataclass
class ExtractArrangementSpec(TransformationSpec[ArrangementSpec]):
    object: WireRef[ObjectSpec]

@register_transformation("ArrangeObjects")
@dataclass
class ArrangeObjectsSpec(TransformationSpec[GridSpec]):
    arrangement: WireRef[ArrangementSpec]
    pattern: WireRef[PatternSpec]
    pool: list[WireRef[ObjectSpec]]

@register_transformation("ApplyMaskToColorMapping")
@dataclass
class ApplyMaskToColorMappingSpec(TransformationSpec[ObjectSpec]):
    mapping: WireRef[MaskToColorMappingSpec]
    object: WireRef[ObjectSpec]
    source_filter: WireRef[FilterSpec] = filter_ref((Access.GET, "mask"))
    target_filter: WireRef[FilterSpec] = filter_ref((Access.SET, "color"))

@register_transformation("ApplyWidthToColorMapping")
@dataclass
class ApplyWidthToColorMappingSpec(TransformationSpec[ObjectSpec]):
    mapping: WireRef[WidthToColorMappingSpec]
    object: WireRef[ObjectSpec]
    source_filter: WireRef[FilterSpec] = filter_ref((Access.GET, "size.width"))
    target_filter: WireRef[FilterSpec] = filter_ref((Access.SET, "color"))

@register_transformation("ChangeColor")
@dataclass
class ChangeColorSpec(TransformationSpec[ObjectSpec]):
    color: WireRef[ColorSpec]
    object: WireRef[ObjectSpec]
    filter: WireRef[FilterSpec] = filter_ref((Access.SET, "color"))

@register_transformation("RemoveObjects")
@dataclass
class RemoveObjectsSpec(TransformationSpec[BaseGroupSpec]):
    object: WireRef[BaseGroupSpec]
    filter: WireRef[FilterSpec] = filter_ref()
