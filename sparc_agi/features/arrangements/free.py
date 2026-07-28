"""Free arrangement: place items by bbox inside the parent object's pixel size."""

import random
from dataclasses import dataclass

from sparc_agi.canvas import Geometry
from sparc_agi.features.arrangements.base import Arrangement
from sparc_agi.features.base import register_feature
from sparc_agi.features.objects.base import Object
from sparc_agi.features.spacing import SpacingValues
from sparc_agi.grid import BBox, bboxes_respect_gap


@register_feature("arrangement.free")
@dataclass
class FreeArrangement(Arrangement):
    """Pixel layout for a group: ``size`` is the parent object's width/height.

    There is no separate canvas type — the group *is* the sized object. Items
    are placed freely by bbox inside that extent. Inherited ``spacing`` is the
    gap between item bboxes and margin from the group's edge.
    """

    def describe(self) -> str:
        return f"arranged randomly within {self.size.describe()} area{self.spacing_phrase()}"

    def instantiate(self, rng: random.Random) -> list[tuple[tuple[int, int], int]]:
        """Free layouts need stamp sizes; use :meth:`layout` instead."""
        del rng
        raise TypeError(
            "FreeArrangement cannot instantiate placements alone; use layout(pool=...)"
        )

    def layout(self, rng: random.Random, pool: list[Object]) -> Geometry:
        """Instantiate pool items and place them inside the parent group's size."""
        if not pool:
            raise ValueError("FreeArrangement.layout requires a non-empty pool")
        width, height = self.size.instantiate(rng)
        sp = self.spacing.instantiate(rng)
        self.sequence.instantiate(rng)

        n_slots = self.count.instantiate(rng) if self.count is not None else max(len(pool), 1)
        indices = [
            idx
            for i in range(n_slots)
            if (idx := self.sequence.index_at(i, n_slots)) != -1
        ]

        last_error: Exception | None = None
        for _ in range(40):
            try:
                return self._layout_once(rng, pool, indices, width, height, sp)
            except ValueError as exc:
                last_error = exc
        assert last_error is not None
        raise last_error

    def _layout_once(
        self,
        rng: random.Random,
        pool: list[Object],
        indices: list[int],
        width: int,
        height: int,
        sp: SpacingValues,
    ) -> Geometry:
        # Place in sequence order so geometries[i] aligns with pool index i
        # when each pool item appears once (PickObject.geometry_index).
        stamps: list[tuple[int, Geometry]] = []
        for idx in indices:
            if idx < 0 or idx >= len(pool):
                continue
            stamp = pool[idx].instantiate(rng)
            if stamp.size()[0] == 0 or stamp.size()[1] == 0:
                continue
            stamps.append((idx, stamp))

        children: list[Geometry] = []
        boxes: list[BBox] = []
        for idx, stamp in stamps:
            sw, sh = stamp.size()
            pos = self._place_one(rng, width, height, sw, sh, sp, boxes, attempts=200)
            if pos is None:
                raise ValueError(
                    f"FreeArrangement.layout could not place pool item {idx} "
                    f"({sw}x{sh}) on {width}x{height}"
                )
            ox, oy = pos
            child = stamp.copy()
            child.x, child.y = ox, oy
            child.slot = idx
            children.append(child)
            boxes.append((ox, oy, sw, sh))
        return Geometry(width=width, height=height, geometries=children)

    def _place_one(
        self,
        rng: random.Random,
        width: int,
        height: int,
        sw: int,
        sh: int,
        sp: SpacingValues,
        existing: list[BBox],
        *,
        attempts: int = 80,
    ) -> tuple[int, int] | None:
        ox_lo = sp.left
        oy_lo = sp.top
        ox_hi = width - sp.right - sw
        oy_hi = height - sp.bottom - sh
        if ox_hi < ox_lo:
            ox_lo, ox_hi = sp.left, sp.left
        if oy_hi < oy_lo:
            oy_lo, oy_hi = sp.top, sp.top

        for _ in range(attempts):
            ox = rng.randint(ox_lo, ox_hi) if ox_hi >= ox_lo else ox_lo
            oy = rng.randint(oy_lo, oy_hi) if oy_hi >= oy_lo else oy_lo
            box: BBox = (ox, oy, sw, sh)
            if all(
                bboxes_respect_gap(box, other, sp.gap_x, sp.gap_y) for other in existing
            ):
                return (ox, oy)
        return None
