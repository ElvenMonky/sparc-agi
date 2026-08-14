from copy import deepcopy
from dataclasses import dataclass
from typing import ClassVar

from sparc_agi.puzzle.features.base import Filter, Mapping
from sparc_agi.puzzle.puzzle import Puzzle
from sparc_agi.puzzle_spec.features.base import Access, FeatureSpec
from sparc_agi.puzzle_spec.features.filter import FilterSpec
from sparc_agi.puzzle_spec.features.mapping import MappingSpec, MaskToColorMappingSpec, WidthToColorMappingSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec
from sparc_agi.puzzle_spec.transformations.base import Transformation, register_transformation
from sparc_agi.puzzle_spec.wire import WireRef

@dataclass
class ApplyMapping[M: MappingSpec](Transformation[ObjectSpec]):
    mapping: WireRef[M]
    object: WireRef[ObjectSpec]
    source_filter: WireRef[FilterSpec]
    target_filter: WireRef[FilterSpec]
    apply_target_trait: ClassVar[str | None] = None

    @classmethod
    def _target_trait(cls, mapping: MappingSpec) -> str:
        trait = cls.apply_target_trait or type(mapping).target_trait
        if trait is None:
            raise ValueError(f"{cls.tag()}: mapping lacks target trait")
        return trait

    @classmethod
    def trace(
        cls,
        mapping: M,
        object: ObjectSpec,
        source_filter: FilterSpec,
        target_filter: FilterSpec,
    ) -> ObjectSpec:
        root = deepcopy(object)
        mapping_cls = type(mapping)
        source_trait = mapping_cls.source_trait
        target_trait = cls._target_trait(mapping)
        if source_trait is None:
            raise ValueError(f"{cls.tag()}: mapping lacks source trait")
        source = source_filter.target(root)
        type(source).validate_trait_access(source_trait, Access.GET)
        target = target_filter.target(root)
        type(target).validate_trait_access(target_trait, Access.SET)
        trait = source.get_trait(source_trait)
        if trait is None:
            raise ValueError(
                f"{cls.tag()}: {type(source).tag()} has no value at trait {source_trait!r}"
            )
        trait = target.get_trait(target_trait)
        if trait is None:
            raise ValueError(
                f"{cls.tag()}: {type(target).tag()} has no value at trait {target_trait!r}"
            )
        target.set_trait(target_trait, type(trait)(value=mapping.value))
        target.alias = f"mapped {target.kind_noun()}"
        return root

    def describe(
        self,
        ctx: Puzzle,
        *,
        mapping: MappingSpec | Mapping,
        object: ObjectSpec,
        source_filter: FilterSpec | Filter,
        target_filter: FilterSpec | Filter,
    ) -> str:
        mapping_cls = type(mapping.spec)
        source_trait = (mapping_cls.source_trait or "").rsplit(".", 1)[-1].replace("_", " ")
        target_trait = type(self)._target_trait(mapping.spec).rsplit(".", 1)[-1].replace("_", " ")
        source = source_filter.spec.refer_target(ctx, object)
        if source_filter.spec.target(object) is target_filter.spec.target(object):
            return f"Change {target_trait} of {source} based on {source_trait}."
        target = target_filter.spec.refer_target(ctx, object)
        return f"Change {target_trait} of {target} based on {source_trait} of {source}."

@register_transformation("ApplyMaskToColorMapping")
@dataclass
class ApplyMaskToColorMapping(ApplyMapping[MaskToColorMappingSpec]):
    pass

@register_transformation("ApplyWidthToColorMapping")
@dataclass
class ApplyWidthToColorMapping(ApplyMapping[WidthToColorMappingSpec]):
    pass

@register_transformation("ApplyWidthToFillColorMapping")
@dataclass
class ApplyWidthToFillColorMapping(ApplyMapping[WidthToColorMappingSpec]):
    apply_target_trait = "fill_color"
