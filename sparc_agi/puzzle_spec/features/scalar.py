import random
from dataclasses import dataclass

from sparc_agi.consts import MAX_COLOR, MAX_COUNT, MAX_DIRECTION, MAX_ORIENTATION, MAX_SIZE, TRANSPARENT_COLOR
from sparc_agi.puzzle.features.base import Scalar
from sparc_agi.puzzle.puzzle import Puzzle
from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature, trait
from sparc_agi.puzzle_spec.range import Range

_COLOR_NAMES: tuple[str, ...] = (
    "black",
    "blue",
    "red",
    "green",
    "yellow",
    "grey",
    "magenta",
    "orange",
    "teal",
    "maroon",
)

@dataclass
class ScalarSpec(FeatureSpec):
    value: Range = trait(default_factory=Range)

    def unstructure(self) -> int | list[int]:
        return self.value.unstructure()

    def instantiate(self, rng: random.Random) -> Scalar:
        return Scalar(spec=self, value=self.value.instantiate(rng))

    def resolved_value(self, instance: Scalar | None = None) -> int | None:
        if isinstance(instance, Scalar):
            return instance.value
        if self.value.is_fixed():
            return self.value.lo
        return None

    def describe(self, ctx: Puzzle, instance: Scalar | None = None) -> str | None:
        value = self.resolved_value(instance)
        return None if value is None else str(value)

@register_feature("color")
@dataclass
class ColorSpec(ScalarSpec):
    value: Range[TRANSPARENT_COLOR, MAX_COLOR] = trait(default_factory=lambda: Range(1, MAX_COLOR))

    def describe(self, ctx: Puzzle, instance: Scalar | None = None) -> str | None:
        logical = self.resolved_value(instance)
        if logical is None:
            return None
        if logical == TRANSPARENT_COLOR:
            return "transparent"
        display = ctx.palette[logical] if 0 <= logical < len(ctx.palette) else logical
        name = _COLOR_NAMES[display] if 0 <= display < len(_COLOR_NAMES) else f"color {display}"
        return f"{name} ({display})"

@register_feature("count")
@dataclass
class CountSpec(ScalarSpec):
    value: Range[1, MAX_COUNT] = trait(default_factory=Range)

@register_feature("width")
@dataclass
class WidthSpec(ScalarSpec):
    value: Range[1, MAX_SIZE] = trait(default_factory=lambda: Range(1, MAX_SIZE))

@register_feature("height")
@dataclass
class HeightSpec(ScalarSpec):
    value: Range[1, MAX_SIZE] = trait(default_factory=lambda: Range(1, MAX_SIZE))

@register_feature("direction")
@dataclass
class DirectionSpec(ScalarSpec):
    value: Range[0, MAX_DIRECTION] = trait(default_factory=Range)

@register_feature("orientation")
@dataclass
class OrientationSpec(ScalarSpec):
    value: Range[0, MAX_ORIENTATION] = trait(default_factory=Range)
