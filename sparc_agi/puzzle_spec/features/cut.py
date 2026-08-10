import random
from dataclasses import InitVar, dataclass, field
from typing import Any

from sparc_agi.consts import MAX_SIZE
from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature
from sparc_agi.puzzle_spec.range import Range

CUT_RANGE = Range[0, MAX_SIZE - 1]

@register_feature("cut")
@dataclass
class CutSpec(FeatureSpec):
    tl: CUT_RANGE = field(default_factory=Range)
    tr: CUT_RANGE = field(default_factory=Range)
    br: CUT_RANGE = field(default_factory=Range)
    bl: CUT_RANGE = field(default_factory=Range)
    value: InitVar[CUT_RANGE | None] = None

    def __post_init__(self, value: CUT_RANGE | None) -> None:
        if value is not None:
            self.tl = self.tr = self.br = self.bl = value

    def unstructure(self) -> dict[str, Any] | int | list[int]:
        if self.tl == self.tr == self.br == self.bl:
            return self.tl.unstructure()
        body: dict[str, int | list[int]] = {}
        for name in ("tl", "tr", "br", "bl"):
            corner = getattr(self, name)
            if corner != Range():
                body[name] = corner.unstructure()
        return body or 0

    def instantiate(self, rng: random.Random) -> tuple[int, int, int, int]:
        return (
            self.tl.instantiate(rng),
            self.tr.instantiate(rng),
            self.br.instantiate(rng),
            self.bl.instantiate(rng),
        )
