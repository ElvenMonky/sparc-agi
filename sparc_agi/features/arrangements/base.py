"""Base class for ``arrangement.*`` feature kinds."""

from dataclasses import dataclass, field

from sparc_agi.features.base import Feature
from sparc_agi.features.scalars.count import Count
from sparc_agi.features.sequence import Sequence
from sparc_agi.features.scalars.size import Size
from sparc_agi.features.spacing import Spacing

@dataclass
class Arrangement(Feature):
    """Placement plan for object copies.

    Universal traits (every arrangement kind):

    - ``size`` — footprint (cells for grid/random/tree; pixels for free)
    - ``sequence`` — which pool indices fill successive slots
    - ``count`` — optional cap / target on how many slots to keep
    - ``spacing`` — gap/margin when projecting placements onto a group
    """

    size: Size
    sequence: Sequence
    count: Count | None = None
    spacing: Spacing = field(default_factory=Spacing)

    def spacing_phrase(self) -> str:
        """E.g. `` with gap 1``, or ``""`` when spacing is default."""
        if self.is_default("spacing"):
            return ""
        parts: list[str] = []
        if not self.spacing.is_default("gap"):
            parts.append(f"gap {self.spacing.gap.describe()}")
        if not self.spacing.is_default("margin"):
            parts.append(f"margin {self.spacing.margin.describe()}")
        if not parts:
            return ""
        return " with " + " and ".join(parts)

    def describe_core(self, kind: str) -> str:
        """``a {size} {kind} using {sequence}``, plus count/spacing when set."""
        text = f"a {self.size.describe()} {kind} using {self.sequence.describe()}"
        if self.count is not None:
            text += f", {self.count.describe()}"
        if not self.is_default("spacing"):
            spacing = self.spacing.describe()
            if spacing:
                text += f", {spacing}"
        return text
