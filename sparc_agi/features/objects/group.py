"""Group object: a pool of items placed according to an arrangement."""

import random
from dataclasses import dataclass, field

from sparc_agi.features.arrangements.base import Arrangement
from sparc_agi.features.base import register_feature
from sparc_agi.features.objects.base import Object
from sparc_agi.features.spacing import Spacing
from sparc_agi.grid import compose_placements


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


@register_feature("object.group")
@dataclass
class Group(Object):
    """Composite object: arrangement + pool (+ spacing)."""

    arrangement: Arrangement
    pool: list[Object] = field(default_factory=list)
    spacing: Spacing = field(default_factory=Spacing)

    def describe(self) -> str:
        refs = [item.refer() for item in self.pool]
        text = f"group of {join_copy_refs(refs)} arranged into {self.arrangement.describe()}"
        if not self.is_default("spacing"):
            spacing = self.spacing.describe()
            if spacing:
                text += f", {spacing}"
        return text

    def instantiate(self, rng: random.Random) -> list[list[int]]:
        if not self.pool:
            raise ValueError("Group.instantiate requires a non-empty pool")
        placements = self.arrangement.instantiate(rng)
        # Fresh pool item per slot so templates (e.g. points) can re-roll color.
        stamps = [self.pool[idx].instantiate(rng) for _, idx in placements]
        slot_placements = [(coord, i) for i, (coord, _) in enumerate(placements)]
        margin, gap = self.spacing.instantiate(rng)
        return compose_placements(slot_placements, stamps, gap=gap, margin=margin)
