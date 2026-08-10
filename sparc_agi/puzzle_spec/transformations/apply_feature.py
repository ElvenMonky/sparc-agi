from copy import deepcopy
from dataclasses import dataclass
from typing import ClassVar

from sparc_agi.puzzle_spec.features.base import Access, FeatureSpec
from sparc_agi.puzzle_spec.features.filter import FilterSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec, PoolItemSpec
from sparc_agi.puzzle_spec.features.scalar import ColorSpec, OrientationSpec
from sparc_agi.puzzle_spec.transformations.base import TransformationSpec, register_transformation
from sparc_agi.puzzle_spec.validate import has_trait_access
from sparc_agi.puzzle_spec.wire import WireRef, filter_ref

@dataclass
class ApplyFeatureSpec[Feature: FeatureSpec](TransformationSpec[ObjectSpec]):
    feature: WireRef[Feature]
    object: WireRef[ObjectSpec]
    filter: WireRef[FilterSpec]
    trait: ClassVar[str]

    @classmethod
    def trace(
        cls,
        feature: Feature,
        object: ObjectSpec,
        filter: FilterSpec | None = None,
    ) -> ObjectSpec:
        root = deepcopy(object)
        slot = PoolItemSpec(value=root)
        if filter is not None:
            slot = filter.apply(slot)
        if slot.value is None:
            raise ValueError(f"{cls.tag()}: filter resolves to removed pool item")
        target = slot.value
        if not has_trait_access(type(target), cls.trait, Access.SET):
            raise ValueError(
                f"{cls.tag()}: {type(target).tag()} lacks settable trait {cls.trait!r}"
            )
        setattr(target, cls.trait, feature)
        return root

@register_transformation("Rotate")
@dataclass
class RotateSpec(ApplyFeatureSpec[OrientationSpec]):
    trait = "orientation"
    filter: WireRef[FilterSpec] = filter_ref((Access.SET, trait), default=None)

@register_transformation("ChangeColor")
@dataclass
class ChangeColorSpec(ApplyFeatureSpec[ColorSpec]):
    trait = "color"
    filter: WireRef[FilterSpec] = filter_ref((Access.SET, trait), default=None)
