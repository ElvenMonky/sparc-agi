import random
from dataclasses import InitVar, dataclass, field
from typing import Any

from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature
from sparc_agi.puzzle_spec.range import Range

@register_feature("margin")
@dataclass
class MarginSpec(FeatureSpec):
    left: Range = field(default_factory=Range)
    right: Range = field(default_factory=Range)
    top: Range = field(default_factory=Range)
    bottom: Range = field(default_factory=Range)
    value: InitVar[Range | None] = None
    x: InitVar[Range | None] = None
    y: InitVar[Range | None] = None

    def __post_init__(
        self,
        value: Range | None,
        x: Range | None,
        y: Range | None,
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
