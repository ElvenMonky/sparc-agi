from dataclasses import dataclass

from sparc_agi.puzzle_spec.features.arrangement import ArrangementSpec
from sparc_agi.puzzle_spec.features.base import FilterSpec
from sparc_agi.puzzle_spec.features.mapping import ColorMappingSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec, GridSpec
from sparc_agi.puzzle_spec.features.pattern import PatternSpec
from sparc_agi.puzzle_spec.features.scalar import ColorSpec, OrientationSpec
from sparc_agi.puzzle_spec.transformations.base import TransformationSpec, register_transformation
from sparc_agi.puzzle_spec.wire import WireRef

@register_transformation("Rotate")
@dataclass
class RotateSpec(TransformationSpec[ObjectSpec]):
    orientation: WireRef[OrientationSpec]
    object: WireRef[ObjectSpec]
    filter: WireRef[FilterSpec]

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

@register_transformation("ApplyColorMapping")
@dataclass
class ApplyColorMappingSpec(TransformationSpec[ObjectSpec]):
    mapping: WireRef[ColorMappingSpec]
    object: WireRef[ObjectSpec]
    source_filter: WireRef[FilterSpec]
    target_filter: WireRef[FilterSpec]

@register_transformation("ChangeColor")
@dataclass
class ChangeColorSpec(TransformationSpec[ObjectSpec]):
    color: WireRef[ColorSpec]
    object: WireRef[ObjectSpec]
    filter: WireRef[FilterSpec]

@register_transformation("RemoveObjects")
@dataclass
class RemoveObjectsSpec(TransformationSpec[BaseGroupSpec]):
    object: WireRef[BaseGroupSpec]
    filter: WireRef[FilterSpec]
