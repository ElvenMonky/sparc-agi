import random
from dataclasses import dataclass, field
from typing import Literal

from sparc_agi.consts import MAX_ORIENTATION, MAX_SIZE
from sparc_agi.puzzle.features.base import Arrangement, Size
from sparc_agi.puzzle.puzzle import Puzzle
from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature, trait, with_article
from sparc_agi.puzzle_spec.features.scalar import ColorSpec, CountSpec, HeightSpec, OrientationSpec, WidthSpec
from sparc_agi.puzzle_spec.range import Range
from sparc_agi.puzzle_spec.sequence import Sequence
from sparc_agi.puzzle_spec.slot import FeatureSlotSpec

_DIRECTION_DX = (1, 1, 0, -1, -1, -1, 0, 1)
_DIRECTION_DY = (0, 1, 1, 1, 0, -1, -1, -1)

def _scan_directions(orientation: int) -> tuple[int, int]:
    secondary = orientation % 8
    if orientation < 8:
        primary = (orientation + 2) % 8
    else:
        primary = (orientation - 2) % 8
    return primary, secondary

def _direction_value(x: int, y: int, direction: int) -> int:
    return x * _DIRECTION_DX[direction] + y * _DIRECTION_DY[direction]

@register_feature("size")
@dataclass
class SizeSpec(FeatureSpec):
    width: WidthSpec = trait(default_factory=WidthSpec)
    height: HeightSpec = trait(default_factory=HeightSpec)
    ratio: Range[1, MAX_SIZE] | None = field(default=None)

    def is_fixed(self) -> bool:
        return self.width.value.is_fixed() and self.height.value.is_fixed()

    def instantiate(self, rng: random.Random) -> Size:
        return Size(
            spec=self,
            width=self.width.instantiate(rng),
            height=self.height.instantiate(rng),
        )

    def describe(self, ctx: Puzzle, instance: Size | None = None) -> str | None:
        width = self.width.describe(ctx, instance.width if instance else None)
        height = self.height.describe(ctx, instance.height if instance else None)
        if width is None or height is None:
            return None
        return f"{width}x{height}"

@register_feature("position")
@dataclass
class PositionSpec(FeatureSpec):
    x: Range[0, MAX_SIZE - 1] = field(default_factory=lambda: Range(0, MAX_SIZE - 1))
    y: Range[0, MAX_SIZE - 1] = field(default_factory=lambda: Range(0, MAX_SIZE - 1))

@register_feature("origin")
@dataclass
class OriginSpec(PositionSpec):
    color: ColorSpec | None = trait(default=None)

    def describe(self, ctx: Puzzle) -> str:
        if self.color and (phrase := self.color.describe(ctx)):
            return f" with {phrase} point at origin"
        return " with point at origin"

@register_feature("arrangement")
@dataclass
class ArrangementSpec(FeatureSpec):
    count: CountSpec | None = trait(default=None)
    size: SizeSpec | None = trait(default=None)

    def instantiate(self, rng: random.Random) -> Arrangement:
        if self.size is None:
            return Arrangement(spec=self, size=None, value=0)
        size = self.size.instantiate(rng)
        width, height = size.width.value, size.height.value
        cells = width * height
        if self.count is None:
            mask = (1 << cells) - 1
        else:
            count = min(max(0, self.count.instantiate(rng).value), cells)
            mask = 0
            for index in rng.sample(range(cells), count):
                mask |= 1 << index
        return Arrangement(spec=self, size=size, value=mask)

    def describe(self, ctx: Puzzle, instance: Arrangement | None = None) -> str:
        if self.size is not None and (
            phrase := self.size.describe(ctx, instance.size if instance else None)
        ):
            return with_article(f"{phrase} grid")
        return "an arrangement"

@dataclass
class ArrangementSlotSpec(FeatureSlotSpec[ArrangementSpec]):
    pass

@register_feature("arrangement.grid")
@dataclass
class GridArrangementSpec(ArrangementSpec):
    size: SizeSpec = trait(default_factory=SizeSpec)
    orientation: OrientationSpec = trait(default_factory=lambda: OrientationSpec(Range(0)))

    def instantiate(self, rng: random.Random) -> Arrangement:
        if self.count is None:
            return super().instantiate(rng)
        size = self.size.instantiate(rng)
        width, height = size.width.value, size.height.value
        cells = width * height
        count = min(max(0, self.count.instantiate(rng).value), cells)
        orientation = self.orientation.instantiate(rng).value
        primary_dir, secondary_dir = _scan_directions(orientation)
        order: list[tuple[int, int, int]] = []
        for y in range(height):
            for x in range(width):
                order.append((
                    _direction_value(x, y, primary_dir),
                    _direction_value(x, y, secondary_dir),
                    y * width + x,
                ))
        order.sort()
        mask = 0
        for _, _, index in order[:count]:
            mask |= 1 << index
        return Arrangement(spec=self, size=size, value=mask)

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
