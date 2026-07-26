from dataclasses import dataclass, field

from sparc_agi.features.base import Feature, register_feature
from sparc_agi.features.color import Color
from sparc_agi.features.orientation import Orientation
from sparc_agi.features.range import Range
from sparc_agi.features.size import Size


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
