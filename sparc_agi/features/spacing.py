"""Spacing: margin around a parent and gap between children.

JSON shortcuts::

    "gap": 1                         → { "x": 1, "y": 1 }
    "gap": { "x": 1, "y": [0, 2] }

    "margin": 0                      → all sides 0
    "margin": { "x": 1, "y": 2 }     → left/right = x, top/bottom = y
    "margin": { "left": 0, "right": 1, "top": 2, "bottom": 2 }
"""

import random
from dataclasses import dataclass, field
from typing import Any

from sparc_agi.features.base import Feature, register_feature
from sparc_agi.range import RangeSpec

def _range_from_raw(raw: Any) -> RangeSpec:
    return raw if isinstance(raw, RangeSpec) else RangeSpec.from_raw(raw)

@dataclass(frozen=True)
class GapSpec:
    """Horizontal / vertical gap between neighboring items or cells."""

    x: RangeSpec = field(default_factory=lambda: RangeSpec(0))
    y: RangeSpec = field(default_factory=lambda: RangeSpec(0))

    @classmethod
    def from_raw(cls, raw: Any) -> GapSpec:
        if isinstance(raw, GapSpec):
            return raw
        if isinstance(raw, (int, list)) or isinstance(raw, RangeSpec):
            r = _range_from_raw(raw)
            return cls(x=r, y=r)
        if isinstance(raw, dict):
            if not raw:
                return cls()
            if "x" in raw or "y" in raw:
                return cls(
                    x=_range_from_raw(raw["x"]) if "x" in raw else RangeSpec(0),
                    y=_range_from_raw(raw["y"]) if "y" in raw else RangeSpec(0),
                )
            raise ValueError(f"gap object must use 'x'/'y', got {raw!r}")
        raise ValueError(f"gap must be a range or {{x, y}} object, got {raw!r}")

    def to_raw(self) -> int | list[int] | dict[str, int | list[int]]:
        if self.x == self.y:
            return self.x.to_raw()
        return {"x": self.x.to_raw(), "y": self.y.to_raw()}

    def describe(self) -> str:
        if self.x == self.y:
            return self.x.describe()
        return f"x {self.x.describe()}, y {self.y.describe()}"

    def sample(self, rng: random.Random) -> tuple[int, int]:
        return (self.x.sample(rng), self.y.sample(rng))

@dataclass(frozen=True)
class MarginSpec:
    """Per-side inset from the parent bbox (left/right/top/bottom)."""

    left: RangeSpec = field(default_factory=lambda: RangeSpec(0))
    right: RangeSpec = field(default_factory=lambda: RangeSpec(0))
    top: RangeSpec = field(default_factory=lambda: RangeSpec(0))
    bottom: RangeSpec = field(default_factory=lambda: RangeSpec(0))

    @classmethod
    def from_raw(cls, raw: Any) -> MarginSpec:
        if isinstance(raw, MarginSpec):
            return raw
        if isinstance(raw, (int, list)) or isinstance(raw, RangeSpec):
            r = _range_from_raw(raw)
            return cls(left=r, right=r, top=r, bottom=r)
        if isinstance(raw, dict):
            if not raw:
                return cls()
            sides = {"left", "right", "top", "bottom"}
            axes = {"x", "y"}
            if sides & raw.keys():
                unknown = set(raw) - sides
                if unknown:
                    raise ValueError(f"margin side object has unknown keys {unknown}")
                return cls(
                    left=_range_from_raw(raw["left"]) if "left" in raw else RangeSpec(0),
                    right=_range_from_raw(raw["right"]) if "right" in raw else RangeSpec(0),
                    top=_range_from_raw(raw["top"]) if "top" in raw else RangeSpec(0),
                    bottom=_range_from_raw(raw["bottom"]) if "bottom" in raw else RangeSpec(0),
                )
            if axes & raw.keys():
                unknown = set(raw) - axes
                if unknown:
                    raise ValueError(f"margin axis object has unknown keys {unknown}")
                x = _range_from_raw(raw["x"]) if "x" in raw else RangeSpec(0)
                y = _range_from_raw(raw["y"]) if "y" in raw else RangeSpec(0)
                return cls(left=x, right=x, top=y, bottom=y)
            raise ValueError(
                f"margin object must use x/y or left/right/top/bottom, got {raw!r}"
            )
        raise ValueError(
            f"margin must be a range, {{x, y}}, or {{left, right, top, bottom}}, got {raw!r}"
        )

    def to_raw(self) -> int | list[int] | dict[str, int | list[int]]:
        if self.left == self.right == self.top == self.bottom:
            return self.left.to_raw()
        if self.left == self.right and self.top == self.bottom:
            return {"x": self.left.to_raw(), "y": self.top.to_raw()}
        out: dict[str, int | list[int]] = {}
        for name in ("left", "right", "top", "bottom"):
            val: RangeSpec = getattr(self, name)
            if val != RangeSpec(0):
                out[name] = val.to_raw()
        return out or 0

    def describe(self) -> str:
        if self.left == self.right == self.top == self.bottom:
            return self.left.describe()
        if self.left == self.right and self.top == self.bottom:
            return f"x {self.left.describe()}, y {self.top.describe()}"
        parts = [
            f"{name} {getattr(self, name).describe()}"
            for name in ("left", "right", "top", "bottom")
            if getattr(self, name) != RangeSpec(0)
        ]
        return ", ".join(parts) if parts else "0"

    def sample(self, rng: random.Random) -> tuple[int, int, int, int]:
        """``(left, right, top, bottom)``."""
        return (
            self.left.sample(rng),
            self.right.sample(rng),
            self.top.sample(rng),
            self.bottom.sample(rng),
        )

@dataclass(frozen=True)
class SpacingValues:
    """Concrete spacing after sampling ranges."""

    left: int = 0
    right: int = 0
    top: int = 0
    bottom: int = 0
    gap_x: int = 0
    gap_y: int = 0

@register_feature("spacing")
@dataclass
class Spacing(Feature):
    margin: MarginSpec = field(default_factory=MarginSpec)
    gap: GapSpec = field(default_factory=GapSpec)

    def describe(self) -> str:
        parts: list[str] = []
        if not self.is_default("margin"):
            parts.append(f"margin {self.margin.describe()}")
        if not self.is_default("gap"):
            parts.append(f"gap {self.gap.describe()}")
        if not parts:
            return ""
        return f"spacing ({', '.join(parts)})"

    def instantiate(self, rng: random.Random) -> SpacingValues:
        left, right, top, bottom = self.margin.sample(rng)
        gap_x, gap_y = self.gap.sample(rng)
        return SpacingValues(
            left=left, right=right, top=top, bottom=bottom, gap_x=gap_x, gap_y=gap_y
        )
