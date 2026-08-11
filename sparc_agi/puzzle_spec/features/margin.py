import random
from dataclasses import InitVar, dataclass, field
from typing import Any

from sparc_agi.consts import MAX_SIZE
from sparc_agi.puzzle_spec.context import PuzzleContext
from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature
from sparc_agi.puzzle_spec.range import Range

MARGIN_RANGE = Range[-MAX_SIZE//2, MAX_SIZE//2]

def _uniform_side(margin: MarginSpec) -> Range | None:
    if margin.left == margin.right == margin.top == margin.bottom:
        return margin.left
    return None

def group_spacing_phrase(margin: MarginSpec, pool: list, ctx: PuzzleContext) -> str:
    if margin == MarginSpec():
        phrase = ""
    elif (side := _uniform_side(margin)) is not None and side.lo == side.hi:
        if side.lo < 0:
            phrase = f" with overflow {-side.lo}"
        elif side.lo > 0:
            phrase = f" with margin {side.lo}"
        else:
            phrase = ""
    else:
        phrase = f" with margin {margin.describe(ctx)}"
    if gaps := [
        side.lo
        for item in pool
        if item.value is not None
        if (side := _uniform_side(item.value.margin)) is not None
        and side.lo == side.hi
        and side.lo > 0
    ]:
        phrase += f" with gap {max(gaps)}"
    return phrase

@register_feature("margin")
@dataclass
class MarginSpec(FeatureSpec):
    left: MARGIN_RANGE = field(default_factory=Range)
    right: MARGIN_RANGE = field(default_factory=Range)
    top: MARGIN_RANGE = field(default_factory=Range)
    bottom: MARGIN_RANGE = field(default_factory=Range)
    value: InitVar[MARGIN_RANGE | None] = None
    x: InitVar[MARGIN_RANGE | None] = None
    y: InitVar[MARGIN_RANGE | None] = None

    def __post_init__(
        self,
        value: MARGIN_RANGE | None,
        x: MARGIN_RANGE | None,
        y: MARGIN_RANGE | None,
    ) -> None:
        if value is not None:
            self.left = self.right = self.top = self.bottom = value
        if x is not None:
            self.left = self.right = x
        if y is not None:
            self.top = self.bottom = y

    def unstructure(self) -> dict[str, Any] | int | list[int]:
        if self.left == self.right == self.top == self.bottom:
            return self.left.unstructure()
        if self.left == self.right and self.top == self.bottom:
            return {"x": self.left.unstructure(), "y": self.top.unstructure()}
        body: dict[str, int | list[int]] = {}
        for name in ("left", "right", "top", "bottom"):
            side = getattr(self, name)
            if side != Range():
                body[name] = side.unstructure()
        return body or 0

    def instantiate(self, rng: random.Random) -> tuple[int, int, int, int]:
        return (
            self.left.instantiate(rng),
            self.right.instantiate(rng),
            self.top.instantiate(rng),
            self.bottom.instantiate(rng),
        )

    def describe(self, ctx: PuzzleContext) -> str:
        if self.left == self.right == self.top == self.bottom:
            return self.left.describe()
        if self.left == self.right and self.top == self.bottom:
            return f"x {self.left.describe()}, y {self.top.describe()}"
        parts = [
            f"{name} {getattr(self, name).describe()}"
            for name in ("left", "right", "top", "bottom")
            if getattr(self, name) != Range()
        ]
        return ", ".join(parts) if parts else "0"
