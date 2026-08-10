from dataclasses import dataclass

from sparc_agi.puzzle_spec.features.base import Access
from sparc_agi.puzzle_spec.features.filter import FilterSpec
from sparc_agi.puzzle_spec.wire import WireRef, filter_ref
from sparc_agi.puzzle_spec.features.mapping import MappingSpec, MaskToColorMappingSpec, WidthToColorMappingSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec
from sparc_agi.puzzle_spec.transformations.base import TransformationSpec, register_transformation
from sparc_agi.puzzle_spec.wire import WireRef

@dataclass
class ApplyMappingSpec[Mapping: MappingSpec](TransformationSpec[ObjectSpec]):
    mapping: WireRef[Mapping]
    object: WireRef[ObjectSpec]
    source_filter: WireRef[FilterSpec]
    target_filter: WireRef[FilterSpec]

    @classmethod
    def trace(
        cls,
        mapping: Mapping,
        object: ObjectSpec,
        source_filter: FilterSpec,
        target_filter: FilterSpec,
    ) -> ObjectSpec:
        return object

@register_transformation("ApplyMaskToColorMapping")
@dataclass
class ApplyMaskToColorMappingSpec(ApplyMappingSpec[MaskToColorMappingSpec]):
    source_filter: WireRef[FilterSpec] = filter_ref((Access.GET, MaskToColorMappingSpec.source_trait))
    target_filter: WireRef[FilterSpec] = filter_ref((Access.SET, MaskToColorMappingSpec.target_trait))

@register_transformation("ApplyWidthToColorMapping")
@dataclass
class ApplyWidthToColorMappingSpec(ApplyMappingSpec[WidthToColorMappingSpec]):
    source_filter: WireRef[FilterSpec] = filter_ref((Access.GET, WidthToColorMappingSpec.source_trait))
    target_filter: WireRef[FilterSpec] = filter_ref((Access.SET, WidthToColorMappingSpec.target_trait))
