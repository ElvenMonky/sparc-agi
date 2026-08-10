from dataclasses import dataclass

from sparc_agi.puzzle_spec.features.base import Access, FeatureSpec, FilterSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec
from sparc_agi.puzzle_spec.features.scalar import ColorSpec, OrientationSpec
from sparc_agi.puzzle_spec.filter import filter_ref
from sparc_agi.puzzle_spec.transformations.base import TransformationSpec, register_transformation
from sparc_agi.puzzle_spec.wire import WireRef

@dataclass
class ApplyFeatureSpec[Feature: FeatureSpec](TransformationSpec[ObjectSpec]):
    feature: WireRef[Feature]
    object: WireRef[ObjectSpec]
    filter: WireRef[FilterSpec]

    @classmethod
    def trace(
        cls,
        feature: Feature,
        object: ObjectSpec,
        filter: FilterSpec | None = None,
    ) -> ObjectSpec:
        return object

@register_transformation("Rotate")
@dataclass
class RotateSpec(ApplyFeatureSpec[OrientationSpec]):
    filter: WireRef[FilterSpec] = filter_ref((Access.SET, "orientation"), default=None)

@register_transformation("ChangeColor")
@dataclass
class ChangeColorSpec(ApplyFeatureSpec[ColorSpec]):
    filter: WireRef[FilterSpec] = filter_ref((Access.SET, "color"), default=None)
