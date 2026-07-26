from __future__ import annotations

import random
from dataclasses import dataclass, field

from sparc_agi.features.base import Feature, register_feature
from sparc_agi.features.color import Color
from sparc_agi.features.orientation import Orientation, transform_xy
from sparc_agi.features.range import Range
from sparc_agi.features.size import Size


def _oriented_grid(
    width: int,
    height: int,
    colors: list[list[int]],
    direction: int,
) -> list[list[int]]:
    """``width``×``height`` pixel grid, transformed by ``direction``.

    Cells outside the painted shape stay ``-1`` (transparent).
    """
    pts = [
        (*transform_xy(x, y, direction), colors[y][x])
        for y in range(height)
        for x in range(width)
    ]
    min_x = min(p[0] for p in pts)
    min_y = min(p[1] for p in pts)
    pts = [(x - min_x, y - min_y, c) for x, y, c in pts]
    out_w = max(p[0] for p in pts) + 1
    out_h = max(p[1] for p in pts) + 1
    grid = [[-1] * out_w for _ in range(out_h)]
    for x, y, color in pts:
        grid[y][x] = color
    return grid


@register_feature("object.sprite")
@dataclass
class Sprite(Feature):
    size: Size
    color: Color = field(default_factory=lambda: Color(value=Range(0, 10)))
    orientation: Orientation = field(default_factory=lambda: Orientation(value=Range(0)))

    def describe(self) -> str:
        extras: list[str] = []
        if not self.is_default("color"):
            extras.append(self.color.describe())
        if not self.is_default("orientation"):
            extras.append(self.orientation.describe())

        # Derived sprites describe relative to their source alias ("input sprite with …").
        if self.source is not None and getattr(self.source, "alias", None):
            base = self.source.alias
        else:
            base = f"{self.size.describe()} sprite"

        if not extras:
            return base
        # Prefer natural phrasing: "input sprite, flipped horizontally"
        # rather than "input sprite with flipped horizontally".
        return f"{base}, {', '.join(extras)}"

    def instantiate(self, rng: random.Random) -> list[list[int]]:
        width, height = self.size.instantiate(rng)
        colors = [
            [self.color.instantiate(rng) for _ in range(width)]
            for _ in range(height)
        ]
        direction = self.orientation.instantiate(rng)
        return _oriented_grid(width, height, colors, direction)
