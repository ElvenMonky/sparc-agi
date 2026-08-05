import random
from dataclasses import dataclass, field
from typing import Any, Self

from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature
from sparc_agi.puzzle_spec.range import Range

@register_feature("margin")
@dataclass
class MarginSpec(FeatureSpec):
    left: Range = field(default_factory=Range)
    right: Range = field(default_factory=Range)
    top: Range = field(default_factory=Range)
    bottom: Range = field(default_factory=Range)

    @classmethod
    def structure(cls, value: Any, _: type) -> Self:
        if isinstance(value, cls):
            return value
        if isinstance(value, dict) and len(value) == 1 and "margin" in value:
            value = value["margin"]
        if isinstance(value, bool):
            raise ValueError(f"margin must be a range or object, got {value!r}")
        if isinstance(value, (int, list, Range)):
            side = Range.structure(value, Range)
            return cls(left=side, right=side, top=side, bottom=side)
        if not isinstance(value, dict):
            raise ValueError(f"margin must be a range or object, got {value!r}")
        if not value:
            return cls()
        sides = {"left", "right", "top", "bottom"}
        axes = {"x", "y"}
        unknown = set(value) - sides - axes
        if unknown:
            raise ValueError(f"margin object has unknown keys {sorted(unknown)}")
        x = Range.structure(value["x"], Range) if "x" in value else Range()
        y = Range.structure(value["y"], Range) if "y" in value else Range()
        return cls(
            left=Range.structure(value["left"], Range) if "left" in value else x,
            right=Range.structure(value["right"], Range) if "right" in value else x,
            top=Range.structure(value["top"], Range) if "top" in value else y,
            bottom=Range.structure(value["bottom"], Range) if "bottom" in value else y,
        )

    def unstructure(self) -> dict[str, Any]:
        if self.left == self.right == self.top == self.bottom:
            body: int | list[int] | dict[str, int | list[int]] = self.left.unstructure()
        elif self.left == self.right and self.top == self.bottom:
            body = {"x": self.left.unstructure(), "y": self.top.unstructure()}
        else:
            body = {}
            for name in ("left", "right", "top", "bottom"):
                side: Range = getattr(self, name)
                if side != Range():
                    body[name] = side.unstructure()
            if not body:
                body = 0
        return body

    def instantiate(self, rng: random.Random) -> tuple[int, int, int, int]:
        return (
            self.left.instantiate(rng),
            self.right.instantiate(rng),
            self.top.instantiate(rng),
            self.bottom.instantiate(rng),
        )
