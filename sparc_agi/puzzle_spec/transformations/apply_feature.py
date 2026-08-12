from copy import deepcopy
from dataclasses import dataclass
from typing import ClassVar

from sparc_agi.puzzle.puzzle import Puzzle
from sparc_agi.puzzle_spec.features.base import Access, FeatureSpec
from sparc_agi.puzzle_spec.features.filter import FilterSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec
from sparc_agi.puzzle_spec.features.scalar import ColorSpec, OrientationSpec
from sparc_agi.puzzle_spec.transformations.base import TransformationSpec, register_transformation
from sparc_agi.puzzle_spec.validate import has_trait_access
from sparc_agi.puzzle_spec.wire import WireRef, filter_ref

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
        target = root if filter is None else filter.target(root)
        if target is None:
            raise ValueError(f"{cls.tag()}: filter resolves to removed pool item")
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

    def alias_stem(
        self,
        *,
        feature: OrientationSpec,
        object: ObjectSpec,
        filter: FilterSpec | None = None,
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
        feature: OrientationSpec,
        object: ObjectSpec,
        filter: FilterSpec | None = None,
    ) -> str:
        target = object if filter is None else filter.target(object) or object
        if not has_trait_access(type(target), self.trait, Access.SET):
            return ""
        phrase = _GEOMETRIC.get(feature.value.lo, "")
        if not phrase:
            return ""
        return phrase.format(target=filter.refer_target(ctx, object) if filter else object.refer(ctx))

@register_transformation("ChangeColor")
@dataclass
class ChangeColorSpec(ApplyFeatureSpec[ColorSpec]):
    trait = "color"
    filter: WireRef[FilterSpec] = filter_ref((Access.SET, trait), default=None)

    def alias_stem(
        self,
        *,
        feature: ColorSpec,
        object: ObjectSpec,
        filter: FilterSpec | None = None,
    ) -> str:
        return "recolored "

    def describe(
        self,
        ctx: Puzzle,
        *,
        feature: ColorSpec,
        object: ObjectSpec,
        filter: FilterSpec | None = None,
    ) -> str:
        target = filter.refer_target(ctx, object) if filter else object.refer(ctx)
        return f"Change color of {target} to {feature.refer(ctx)}."
