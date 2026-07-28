"""Tree arrangement: grow an 8-connected cluster on a virtual grid."""

import random
from dataclasses import dataclass, field

from sparc_agi.features.arrangements.base import Arrangement
from sparc_agi.features.base import register_feature
from sparc_agi.features.scalars.range import Range


# Eight neighbors (no center).
_DIRS8 = (
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)


def grow_tree_cells(
    rng: random.Random,
    target: int,
    *,
    root: tuple[int, int] = (0, 0),
    bounds: tuple[int, int] | None = None,
) -> list[tuple[int, int]]:
    """Grow an 8-connected cluster of ``target`` cells from ``root``.

    When ``bounds`` is ``(width, height)``, growth stays inside that rectangle.
    When ``bounds`` is ``None``, growth is unbounded (caller crops afterward).
    """
    target = max(1, target)
    cells = [root]
    occupied = {root}
    while len(cells) < target:
        candidates: list[tuple[int, int]] = []
        for px, py in cells:
            for dx, dy in _DIRS8:
                nx, ny = px + dx, py + dy
                if (nx, ny) in occupied:
                    continue
                if bounds is not None:
                    width, height = bounds
                    if not (0 <= nx < width and 0 <= ny < height):
                        continue
                candidates.append((nx, ny))
        if not candidates:
            break
        nxt = candidates[rng.randrange(len(candidates))]
        cells.append(nxt)
        occupied.add(nxt)
    return cells


@dataclass
class Origin:
    """Optional fixed root cell for a tree arrangement."""

    x: Range = field(default_factory=lambda: Range(0))
    y: Range = field(default_factory=lambda: Range(0))

    def instantiate(self, rng: random.Random) -> tuple[int, int]:
        return (self.x.sample(rng), self.y.sample(rng))


@register_feature("arrangement.tree")
@dataclass
class TreeArrangement(Arrangement):
    """Virtual-grid cluster grown from a root via 8-connected steps.

    Starts at ``origin`` (or a random in-bounds cell). Each new cell is an empty
    8-neighbor of some already placed cell. ``count`` is the growth target;
    ``spacing`` applies when the parent group projects cells to pixels.
    """

    origin: Origin | None = None

    def describe(self) -> str:
        text = f"arranged into a tree that fits within {self.size.describe()} area"
        text += self.spacing_phrase()
        if self.origin is not None:
            text += f", origin ({self.origin.x.describe()}, {self.origin.y.describe()})"
        return text

    def instantiate(self, rng: random.Random) -> list[tuple[tuple[int, int], int]]:
        width, height = self.size.instantiate(rng)
        if width <= 0 or height <= 0:
            return []
        target = self.count.instantiate(rng) if self.count is not None else width * height
        target = max(1, min(target, width * height))

        if self.origin is not None:
            ox, oy = self.origin.instantiate(rng)
            ox = min(max(ox, 0), width - 1)
            oy = min(max(oy, 0), height - 1)
            root = (ox, oy)
        else:
            root = (rng.randrange(width), rng.randrange(height))

        cells = grow_tree_cells(rng, target, root=root, bounds=(width, height))

        self.sequence.instantiate(rng)
        n = len(cells)
        out: list[tuple[tuple[int, int], int]] = []
        for i, coord in enumerate(cells):
            idx = self.sequence.index_at(i, n)
            if idx == -1:
                continue
            out.append((coord, idx))
        return out
