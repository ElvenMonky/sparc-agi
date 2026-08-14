from copy import deepcopy
from dataclasses import dataclass, field
from typing import ClassVar

from sparc_agi.puzzle.features.base import Filter, Scalar
from sparc_agi.puzzle.puzzle import Puzzle
from sparc_agi.puzzle_spec.features.base import Access, FeatureSpec
from sparc_agi.puzzle_spec.features.filter import FilterSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec
from sparc_agi.puzzle_spec.features.scalar import ColorSpec, OrientationSpec
from sparc_agi.puzzle_spec.features.arrangement import SizeSpec
from sparc_agi.puzzle_spec.transformations.base import TransformationSpec, register_transformation
from sparc_agi.puzzle_spec.wire import WireRef

_GEOMETRIC: dict[int, str] = {
    0: "",
    1: "Rotate {target} 45 degrees counterclockwise.",
    2: "Rotate {target} 90 degrees counterclockwise.",
    3: "Rotate {target} 135 degrees counterclockwise.",
    4: "Rotate {target} 180 degrees.",
    5: "Rotate {target} 135 degrees clockwise.",
    6: "Rotate {target} 90 degrees clockwise.",
    7: "Rotate {target} 45 degrees clockwise.",
    8: "Flip {target} vertically.",
    9: "Flip {target} vertically and rotated 45 degrees counterclockwise.",
    10: "Flip {target} over the main diagonal.",
    11: "Flip {target} over the main diagonal and rotated 45 degrees counterclockwise.",
    12: "Flip {target} horizontally.",
    13: "Flip {target} horizontally and rotated 45 degrees counterclockwise.",
    14: "Flip {target} over the anti-diagonal.",
    15: "Flip {target} over the anti-diagonal and rotated 45 degrees counterclockwise.",
}

@dataclass
class ApplyFeature[Feature: FeatureSpec](TransformationSpec[ObjectSpec]):
    feature: WireRef[Feature]
    object: WireRef[ObjectSpec]
    filter: WireRef[FilterSpec]
    trait: ClassVar[str]

    @classmethod
    def trace(
        cls,
        feature: Feature,
        object: ObjectSpec,
        filter: FilterSpec,
    ) -> ObjectSpec:
        root = deepcopy(object)
        target = filter.target(root)
        type(target).validate_trait_access(cls.trait, Access.SET)
        setattr(target, cls.trait, feature)
        return root

    def describe(
        self,
        ctx: Puzzle,
        *,
        feature: Feature,
        object: ObjectSpec,
        filter: FilterSpec | Filter,
    ) -> str:
        return f"Change {self.trait} of {filter.spec.refer_target(ctx, object)} to {feature.refer(ctx)}."

@register_transformation("Rotate")
@dataclass
class Rotate(ApplyFeature[OrientationSpec]):
    trait = "orientation"
    filter: WireRef[FilterSpec] = field(default=None)

    def alias_stem(
        self,
        *,
        feature: OrientationSpec,
        object: ObjectSpec,
        filter: FilterSpec,
    ) -> str:
        phrase = _GEOMETRIC.get(feature.value.lo, "")
        if phrase.startswith("Flip"):
            return "flipped "
        if phrase.startswith("Rotate"):
            return "rotated "
        return ""

    def describe(
        self,
        ctx: Puzzle,
        *,
        feature: OrientationSpec | Scalar,
        object: ObjectSpec,
        filter: FilterSpec | Filter,
    ) -> str:
        orientation = feature.spec.resolved_value(feature)
        if orientation is None:
            return ""
        phrase = _GEOMETRIC.get(orientation, "")
        if not phrase:
            return ""
        return phrase.format(target=filter.spec.refer_target(ctx, object))

@register_transformation("ChangeColor")
@dataclass
class ChangeColor(ApplyFeature[ColorSpec]):
    trait = "color"
    filter: WireRef[FilterSpec] = field(default=None)

    def alias_stem(
        self,
        *,
        feature: ColorSpec,
        object: ObjectSpec,
        filter: FilterSpec,
    ) -> str:
        return "recolored "

    def describe(
        self,
        ctx: Puzzle,
        *,
        feature: ColorSpec | Scalar,
        object: ObjectSpec,
        filter: FilterSpec | Filter,
    ) -> str:
        return f"Change color of {filter.spec.refer_target(ctx, object)} to {feature.refer(ctx)}."

@register_transformation("ChangeFillColor")
@dataclass
class ChangeFillColor(ApplyFeature[ColorSpec]):
    trait = "fill_color"
    filter: WireRef[FilterSpec] = field(default=None)

    def alias_stem(
        self,
        *,
        feature: ColorSpec,
        object: ObjectSpec,
        filter: FilterSpec,
    ) -> str:
        return "recolored "

    def describe(
        self,
        ctx: Puzzle,
        *,
        feature: ColorSpec | Scalar,
        object: ObjectSpec,
        filter: FilterSpec | Filter,
    ) -> str:
        return f"Change fill color of {filter.spec.refer_target(ctx, object)} to {feature.refer(ctx)}."

@register_transformation("Resize")
@dataclass
class Resize(ApplyFeature[SizeSpec]):
    trait = "size"
    filter: WireRef[FilterSpec] = field(default=None)

    def alias_stem(
        self,
        *,
        feature: SizeSpec,
        object: ObjectSpec,
        filter: FilterSpec,
    ) -> str:
        return "resized "