from copy import deepcopy
from dataclasses import dataclass
from typing import ClassVar

from sparc_agi.puzzle.puzzle import Puzzle
from sparc_agi.puzzle_spec.features.base import Access, FeatureSpec
from sparc_agi.puzzle_spec.features.filter import FilterSpec
from sparc_agi.puzzle_spec.features.mapping import MappingSpec, MaskToColorMappingSpec, WidthToColorMappingSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec
from sparc_agi.puzzle_spec.features.scalar import ColorSpec
from sparc_agi.puzzle_spec.transformations.base import TransformationSpec, register_transformation
from sparc_agi.puzzle_spec.wire import WireRef, filter_ref

@dataclass
class ApplyMappingSpec[Mapping: MappingSpec](TransformationSpec[ObjectSpec]):
    mapping: WireRef[Mapping]
    object: WireRef[ObjectSpec]
    source_filter: WireRef[FilterSpec]
    target_filter: WireRef[FilterSpec]
    apply_target_trait: ClassVar[str | None] = None

    @classmethod
    def _target_trait(cls, mapping: Mapping) -> str:
        trait = cls.apply_target_trait or type(mapping).target_trait
        if trait is None:
            raise ValueError(f"{cls.tag()}: mapping lacks target trait")
        return trait

    @classmethod
    def trace(
        cls,
        mapping: Mapping,
        object: ObjectSpec,
        source_filter: FilterSpec,
        target_filter: FilterSpec,
    ) -> ObjectSpec:
        root = deepcopy(object)
        source = source_filter.target(root)
        target = target_filter.target(root)
        if source is None or target is None:
            raise ValueError(f"{cls.tag()}: filter resolves to removed pool item")
        mapping_cls = type(mapping)
        source_trait = mapping_cls.source_trait
        target_trait = cls._target_trait(mapping)
        if source_trait is None:
            raise ValueError(f"{cls.tag()}: mapping lacks source trait")
        if not type(source).has_trait_access(source_trait, Access.GET):
            raise ValueError(
                f"{cls.tag()}: {type(source).tag()} lacks gettable trait {source_trait!r}"
            )
        if not type(target).has_trait_access(target_trait, Access.SET):
            raise ValueError(
                f"{cls.tag()}: {type(target).tag()} lacks settable trait {target_trait!r}"
            )
        source.get_trait(source_trait)
        target.set_trait(target_trait, ColorSpec(value=mapping.value))
        target.alias = f"mapped {target.kind_noun()}"
        return root

    def describe(
        self,
        ctx: Puzzle,
        *,
        mapping: Mapping,
        object: ObjectSpec,
        source_filter: FilterSpec,
        target_filter: FilterSpec,
    ) -> str:
        mapping_cls = type(mapping)
        source_trait = (mapping_cls.source_trait or "").rsplit(".", 1)[-1].replace("_", " ")
        target_trait = type(self)._target_trait(mapping).rsplit(".", 1)[-1].replace("_", " ")
        source = source_filter.refer_target(ctx, object)
        if source_filter.target(object) is target_filter.target(object):
            return f"Change {target_trait} of {source} based on {source_trait}."
        target = target_filter.refer_target(ctx, object)
        return f"Change {target_trait} of {target} based on {source_trait} of {source}."

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

@register_transformation("ApplyWidthToFillColorMapping")
@dataclass
class ApplyWidthToFillColorMappingSpec(ApplyMappingSpec[WidthToColorMappingSpec]):
    apply_target_trait = "fill_color"
    source_filter: WireRef[FilterSpec] = filter_ref((Access.GET, WidthToColorMappingSpec.source_trait))
    target_filter: WireRef[FilterSpec] = filter_ref((Access.SET, "fill_color"))
