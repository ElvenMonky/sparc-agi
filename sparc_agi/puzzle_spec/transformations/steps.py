from dataclasses import dataclass

from sparc_agi.puzzle_spec.transformations.base import TransformationSpec, WireRef, register_transformation

@register_transformation("Rotate")
@dataclass
class RotateSpec(TransformationSpec):
    orientation: WireRef
    object: WireRef

@register_transformation("ExtractArrangement")
@dataclass
class ExtractArrangementSpec(TransformationSpec):
    object: WireRef

@register_transformation("ArrangeObjects")
@dataclass
class ArrangeObjectsSpec(TransformationSpec):
    arrangement: WireRef
    pattern: WireRef
    pool: list[WireRef]

@register_transformation("ApplyColorMapping")
@dataclass
class ApplyColorMappingSpec(TransformationSpec):
    mapping: WireRef
    object: WireRef
    source_filter: WireRef
    target_filter: WireRef

@register_transformation("ChangeColor")
@dataclass
class ChangeColorSpec(TransformationSpec):
    color: WireRef
    object: WireRef
    filter: WireRef

@register_transformation("RemoveObjects")
@dataclass
class RemoveObjectsSpec(TransformationSpec):
    object: WireRef
    filter: WireRef
