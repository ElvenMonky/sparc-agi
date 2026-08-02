"""Group object: a pool of items placed according to an arrangement."""

import random
from dataclasses import dataclass, field

from sparc_agi.geometry import Geometry
from sparc_agi.features.arrangements.base import Arrangement
from sparc_agi.features.base import register_feature
from sparc_agi.features.objects.base import Object

def join_copy_refs(refs: list[str]) -> str:
    """Join object refs as ``copies of A and B`` / ``copies of A, B, and C``."""
    if not refs:
        return "no items"
    if len(refs) == 1:
        return f"copies of {refs[0]}"
    if len(refs) == 2:
        return f"copies of {refs[0]} and {refs[1]}"
    *rest, last = refs
    return "copies of " + ", ".join(rest) + f", and {last}"

def _count_phrase(arrangement: Arrangement) -> str | None:
    if arrangement.count is None:
        return None
    return arrangement.count.value.describe()

@register_feature("object.group")
@dataclass
class Group(Object):
    """Composite object: arrangement + pool.

    Instantiation yields a :class:`~sparc_agi.canvas.Geometry` tree: children are
    pool item instances placed at pixel offsets (cell layouts use arrangement
    spacing; free layouts place by bbox).
    """

    arrangement: Arrangement
    pool: list[Object] = field(default_factory=list)

    def describe(self) -> str:
        arr = self.arrangement
        count = _count_phrase(arr)
        kind = type(arr).__feature_name__

        if kind == "arrangement.free":
            n = count if count is not None else str(len(self.pool))
            head = f"group of {n} objects {arr.describe()}"
            members = "; ".join(item.describe() for item in self.pool)
            return f"{head}: {members}" if members else head

        if (
            kind == "arrangement.tree"
            and len(self.pool) == 1
            and type(self.pool[0]).__feature_name__ == "object.point"
        ):
            point = self.pool[0]
            color = point.color.describe()  # type: ignore[attr-defined]
            if count is not None:
                return f"group of {count} {color} points {arr.describe()}"
            return f"group of {color} points {arr.describe()}"

        members = ", ".join(item.describe() for item in self.pool)
        if count is not None:
            return f"group of {count} objects ({members}) {arr.describe()}"
        return f"group of {members} {arr.describe()}"

    def instantiate(self, rng: random.Random) -> Geometry:
        if not self.pool:
            raise ValueError("Group.instantiate requires a non-empty pool")
        layout = getattr(self.arrangement, "layout", None)
        if callable(layout):
            return layout(rng, self.pool)

        placements = self.arrangement.instantiate(rng)
        stamps = [self.pool[idx].instantiate(rng) for _, idx in placements]
        sp = self.arrangement.spacing.instantiate(rng)
        size = self.arrangement.size
        wv, hv = size.width.value, size.height.value
        grid_w = wv.lo if wv.lo == wv.hi else None
        grid_h = hv.lo if hv.lo == hv.hi else None
        if grid_w is None:
            grid_w = max((x for (x, _), _ in placements), default=-1) + 1
        if grid_h is None:
            grid_h = max((y for (_, y), _ in placements), default=-1) + 1

        cell_w = max((s.size()[0] for s in stamps), default=1)
        cell_h = max((s.size()[1] for s in stamps), default=1)
        stride_x = cell_w + sp.gap_x
        stride_y = cell_h + sp.gap_y

        children: list[Geometry] = []
        for i, ((gx, gy), pool_idx) in enumerate(placements):
            child = stamps[i].copy()
            child.x = sp.left + gx * stride_x
            child.y = sp.top + gy * stride_y
            child.slot = pool_idx
            children.append(child)

        content_w = (grid_w - 1) * stride_x + cell_w if grid_w > 0 else 0
        content_h = (grid_h - 1) * stride_y + cell_h if grid_h > 0 else 0
        width = content_w + sp.left + sp.right
        height = content_h + sp.top + sp.bottom
        return Geometry(width=max(width, 0), height=max(height, 0), geometries=children)
