from dataclasses import dataclass, field

from sparc_agi.features.base import Feature, Sequence, register_feature
from sparc_agi.features.count import Count
from sparc_agi.features.footprint import Footprint
from sparc_agi.features.orientation import Orientation
from sparc_agi.features.range import Range


@register_feature("arrangement.grid")
@dataclass
class GridArrangement(Feature):
    footprint: Footprint
    sequence: Sequence
    orientation: Orientation = field(default_factory=lambda: Orientation(value=Range(0)))
    # None / omitted → place as many as possible.
    count: Count | None = None

    def placement_count(self) -> int:
        """How many child slots this arrangement fills when traced."""
        if self.count is not None:
            n = self.count.value
            if n.lo != n.hi:
                raise ValueError(f"arrangement count must be exact for tracing, got {n.to_raw()!r}")
            return n.lo
        # As many as possible: fill the footprint grid.
        w, h = self.footprint.size.width.value, self.footprint.size.height.value
        if w.lo != w.hi or h.lo != h.hi:
            raise ValueError(
                "footprint size must be exact when count is omitted, "
                f"got width={w.to_raw()!r} height={h.to_raw()!r}"
            )
        return w.lo * h.lo

    def describe(self) -> str:
        size = self.footprint.size.describe()
        text = f"a {size} grid using {self.sequence.cycle} pattern"
        scan = self.orientation.grid_scan_phrase()
        if scan:
            text += f", applied {scan}"
        if self.count is not None:
            text += f", {self.count.describe()}"
        return text
