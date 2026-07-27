"""Sprite: a rectangular pattern of points on a grid arrangement."""

import random
from dataclasses import dataclass, field

from sparc_agi.features.arrangements.grid import GridArrangement
from sparc_agi.features.base import register_feature
from sparc_agi.features.color import Color
from sparc_agi.features.objects.base import Object
from sparc_agi.features.objects.group import Group
from sparc_agi.features.objects.point import Point
from sparc_agi.features.orientation import Orientation
from sparc_agi.features.range import Range
from sparc_agi.features.sequence import Sequence
from sparc_agi.features.size import Size
from sparc_agi.grid import apply_orientation


@register_feature("object.sprite")
@dataclass
class Sprite(Object):
    """Dense rectangle of points.

    Traits: ``size``, ``color``, ``orientation``. Grid layout is not a trait —
    expand via :meth:`as_group` when a pool/arrangement is needed.
    """

    size: Size
    color: Color = field(default_factory=lambda: Color(value=Range(0, 9)))
    orientation: Orientation = field(default_factory=lambda: Orientation(value=Range(0)))

    def as_group(self) -> Group:
        """Expand to a group of points on a grid arrangement (identity scan)."""
        return Group(
            arrangement=GridArrangement(
                size=self.size,
                sequence=Sequence(cycle=[0]),
            ),
            pool=[Point(color=self.color)],
        )

    def describe(self) -> str:
        extras: list[str] = []
        if not self.is_default("color"):
            extras.append(self.color.describe())
        if not self.is_default("orientation"):
            extras.append(self.orientation.describe())

        if self.source is not None and getattr(self.source, "alias", None):
            base = self.source.alias
        else:
            base = f"{self.size.describe()} sprite"

        if not extras:
            return base
        return f"{base}, {', '.join(extras)}"

    def instantiate(self, rng: random.Random) -> list[list[int]]:
        grid = self.as_group().instantiate(rng)
        direction = self.orientation.instantiate(rng)
        if direction == 0:
            return grid
        return apply_orientation(grid, direction)
