from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from sparc_agi.puzzle_spec.features.base import Access, FeatureSpec
from sparc_agi.puzzle_spec.features.filter import FilterSpec
from sparc_agi.puzzle_spec.features.mapping import MappingSpec, MaskToColorMappingSpec, WidthToColorMappingSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec, PoolItemSpec
from sparc_agi.puzzle_spec.features.scalar import ColorSpec
from sparc_agi.puzzle_spec.slot import FeatureSlotSpec
from sparc_agi.puzzle_spec.transformations.base import TransformationSpec, register_transformation
from sparc_agi.puzzle_spec.validate import has_trait_access
from sparc_agi.puzzle_spec.wire import WireRef, filter_ref

def _read_trait(obj: ObjectSpec, path: str) -> FeatureSpec | None:
    current: Any = obj
    for part in path.split("."):
        if current is None:
            return None
        value = getattr(current, part, None)
        if value is None:
            return None
        current = value.value if isinstance(value, FeatureSlotSpec) else value
    return current

def _write_trait(obj: ObjectSpec, path: str, feature: FeatureSpec) -> None:
    current: Any = obj
    *prefix, leaf = path.split(".")
    for part in prefix:
        value = getattr(current, part)
        current = value.value if isinstance(value, FeatureSlotSpec) else value
    slot = getattr(current, leaf)
    if isinstance(slot, FeatureSlotSpec):
        slot.value = feature
    else:
        setattr(current, leaf, feature)

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
        root = deepcopy(object)
        slot = PoolItemSpec(value=root)
        source = source_filter.apply(slot).value
        target = target_filter.apply(slot).value
        if source is None or target is None:
            raise ValueError(f"{cls.tag()}: filter resolves to removed pool item")
        mapping_cls = type(mapping)
        source_trait = mapping_cls.source_trait
        target_trait = mapping_cls.target_trait
        if source_trait is None or target_trait is None:
            raise ValueError(f"{cls.tag()}: mapping lacks source or target trait")
        if not has_trait_access(type(source), source_trait, Access.GET):
            raise ValueError(
                f"{cls.tag()}: {type(source).tag()} lacks gettable trait {source_trait!r}"
            )
        if not has_trait_access(type(target), target_trait, Access.SET):
            raise ValueError(
                f"{cls.tag()}: {type(target).tag()} lacks settable trait {target_trait!r}"
            )
        _read_trait(source, source_trait)
        _write_trait(target, target_trait, ColorSpec(value=mapping.value))
        return root

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
