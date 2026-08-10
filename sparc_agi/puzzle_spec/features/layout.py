from dataclasses import dataclass, field
from typing import Literal

from sparc_agi.consts import MAX_COUNT, MAX_ORIENTATION, MAX_SIZE
from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature, trait
from sparc_agi.puzzle_spec.features.scalar import ColorSpec, CountSpec, HeightSpec, OrientationSpec, WidthSpec
from sparc_agi.puzzle_spec.range import Range
from sparc_agi.puzzle_spec.slot import FeatureSlotSpec

@register_feature("size")
@dataclass
class SizeSpec(FeatureSpec):
    width: WidthSpec | None = trait(default=None)
    height: HeightSpec | None = trait(default=None)
    ratio: Range[1, MAX_SIZE] | None = field(default=None)

@register_feature("position")
@dataclass
class PositionSpec(FeatureSpec):
    x: Range[0, MAX_SIZE - 1] = field(default_factory=lambda: Range(0, MAX_SIZE - 1))
    y: Range[0, MAX_SIZE - 1] = field(default_factory=lambda: Range(0, MAX_SIZE - 1))

@register_feature("origin")
@dataclass
class OriginSpec(PositionSpec):
    color: ColorSpec | None = trait(default=None)

@register_feature("pattern")
@dataclass
class PatternSpec(FeatureSpec):
    prefix: list[int] = field(default_factory=list)
    pattern: list[int] = field(default_factory=list)

@dataclass
class PatternSlotSpec(FeatureSlotSpec[PatternSpec]):
    pass

@register_feature("pattern.linear")
@dataclass
class LinearPatternSpec(PatternSpec):
    direction: OrientationSpec = trait(default_factory=lambda: OrientationSpec(Range(0)))

@register_feature("arrangement")
@dataclass
class ArrangementSpec(FeatureSpec):
    count: CountSpec | None = trait(default=None)
    size: SizeSpec | None = trait(default=None)

@dataclass
class ArrangementSlotSpec(FeatureSlotSpec[ArrangementSpec]):
    pass

@register_feature("arrangement.grid")
@dataclass
class GridArrangementSpec(ArrangementSpec):
    direction: OrientationSpec = trait(default_factory=lambda: OrientationSpec(Range(0)))

@dataclass
class RaySpec:
    direction: Range[0, MAX_ORIENTATION] = field(default_factory=lambda: Range(0, MAX_ORIENTATION))
    count: Range[1, MAX_COUNT] = field(default_factory=lambda: Range(1, MAX_COUNT))

@register_feature("arrangement.star")
@dataclass
class StarArrangementSpec(ArrangementSpec):
    rays: list[RaySpec] = field(default_factory=list)
    origin: PositionSpec | None = trait(default=None)
    order: Literal["same", "next", "random"] = field(default="same")
    gap: PatternSpec | None = trait(default=None)
    growth: PatternSpec | None = trait(default=None)
    turn: PatternSpec | None = trait(default=None)

@register_feature("arrangement.tree")
@dataclass
class TreeArrangementSpec(ArrangementSpec):
    origin: PositionSpec | None = trait(default=None)
