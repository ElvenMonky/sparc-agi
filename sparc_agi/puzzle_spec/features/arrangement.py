from dataclasses import dataclass, field
from typing import Literal

from sparc_agi.consts import MAX_ORIENTATION, MAX_SIZE
from sparc_agi.puzzle_spec.context import PuzzleContext
from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature, trait
from sparc_agi.puzzle_spec.features.scalar import ColorSpec, CountSpec, HeightSpec, OrientationSpec, WidthSpec
from sparc_agi.puzzle_spec.range import Range
from sparc_agi.puzzle_spec.sequence import Sequence
from sparc_agi.puzzle_spec.slot import FeatureSlotSpec

@register_feature("size")
@dataclass
class SizeSpec(FeatureSpec):
    width: WidthSpec = trait(default_factory=WidthSpec)
    height: HeightSpec = trait(default_factory=HeightSpec)
    ratio: Range[1, MAX_SIZE] | None = field(default=None)

    def is_fixed(self) -> bool:
        return self.width.value.is_fixed() and self.height.value.is_fixed()

    def describe(self, ctx: PuzzleContext) -> str | None:
        if not self.is_fixed():
            return None
        return f"{self.width.value.describe()}x{self.height.value.describe()}"

@register_feature("position")
@dataclass
class PositionSpec(FeatureSpec):
    x: Range[0, MAX_SIZE - 1] = field(default_factory=lambda: Range(0, MAX_SIZE - 1))
    y: Range[0, MAX_SIZE - 1] = field(default_factory=lambda: Range(0, MAX_SIZE - 1))

@register_feature("origin")
@dataclass
class OriginSpec(PositionSpec):
    color: ColorSpec | None = trait(default=None)

    def describe(self, ctx: PuzzleContext) -> str:
        if self.color and (phrase := self.color.describe(ctx)):
            return f" with {phrase} point at origin"
        return " with point at origin"

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
    length: Range[1, MAX_SIZE] = field(default_factory=lambda: Range(1, MAX_SIZE))

class GrowthSpec(Sequence[-MAX_SIZE // 2, MAX_SIZE // 2]):
    pass

class TurnSpec(Sequence[0, MAX_ORIENTATION // 2]):
    pass

@register_feature("arrangement.star")
@dataclass
class StarArrangementSpec(ArrangementSpec):
    rays: list[RaySpec] = field(default_factory=list)
    origin: PositionSpec | None = trait(default=None)
    order: Literal["same", "next", "random"] = field(default="same")
    growth: GrowthSpec | None = trait(default=None)
    turn: TurnSpec | None = trait(default=None)

@register_feature("arrangement.tree")
@dataclass
class TreeArrangementSpec(ArrangementSpec):
    origin: PositionSpec | None = trait(default=None)
