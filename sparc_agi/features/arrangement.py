"""Arrangement features: footprint coordinates paired with pool indices."""

from __future__ import annotations

import random
from dataclasses import dataclass

from sparc_agi.features.base import Feature, register_feature
from sparc_agi.features.sequence import Sequence


@register_feature("arrangement")
@dataclass
class Arrangement(Feature):
    """Place pool items onto a footprint using a sequence of pool indices.

    Instantiation yields ``[((x, y), pool_index), ...]`` with empty (``-1``)
    sequence slots removed.
    """

    footprint: Feature
    sequence: Sequence

    def describe(self) -> str:
        # Prefer the compact grid phrasing used in transformation steps.
        size = getattr(getattr(self.footprint, "size", None), "describe", lambda: None)()
        if size is None:
            return f"{self.footprint.describe()} using {self.sequence.describe()}"
        text = f"a {size} grid using {self.sequence.describe()}"
        scan = None
        orientation = getattr(self.footprint, "orientation", None)
        if orientation is not None:
            scan = orientation.grid_scan_phrase()
        if scan:
            text += f", applied {scan}"
        return text

    def instantiate(self, rng: random.Random) -> list[tuple[tuple[int, int], int]]:
        coords = self.footprint.instantiate(rng)
        self.sequence.instantiate(rng)  # (prefix, cycle, suffix); sequence is data-only
        n = len(coords)
        out: list[tuple[tuple[int, int], int]] = []
        for i, coord in enumerate(coords):
            idx = self.sequence.index_at(i, n)
            if idx == -1:
                continue
            out.append((coord, idx))
        return out
