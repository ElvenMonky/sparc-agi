from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from sparc_agi.features.arrangements.base import Arrangement
from sparc_agi.features.base import Feature
from sparc_agi.grid import Grid, Placement
from sparc_agi.transformations.base import Transformation, register_transformation


def _placements_from_grid(grid: Grid) -> list[Placement]:
    """Occupied cells (positive colors) as pool-index-0 placements."""
    out: list[Placement] = []
    for y, row in enumerate(grid):
        for x, val in enumerate(row):
            if val > 0:
                out.append(((x, y), 0))
    return out


@register_transformation("ExtractArrangement")
@dataclass
class ExtractArrangement(Transformation):
    """Pull a read-only arrangement off an object; inputs ``[object]`` → ``arrangement``.

    At instantiate time, recovers placements from occupied cells of the object grid
    (so the sampled glyph pattern is preserved for later ArrangeObjects).
    """

    input_features = ("object",)
    output_feature = "arrangement"

    def apply(self, inputs: Sequence[Feature], *, step: int, **_: object) -> Feature:
        (obj,) = inputs
        if type(obj).__feature_family__ != "object":
            raise TypeError(
                f"ExtractArrangement expects an object feature, got {type(obj).__feature_name__}"
            )
        if not hasattr(obj, "arrangement"):
            raise TypeError(f"{type(obj).__name__} has no arrangement to extract")
        arrangement = obj.arrangement
        if not isinstance(arrangement, Arrangement):
            raise TypeError(
                f"{type(obj).__name__}.arrangement must be an Arrangement, "
                f"got {type(arrangement).__name__}"
            )
        out = arrangement.derived()
        out.alias = f"arrangement from step {step}"
        return out

    def instantiate(
        self,
        inputs: Sequence[Any],
        *,
        step: int,
        feature_inputs: Sequence[Feature] | None = None,
    ) -> list[Placement]:
        del step, feature_inputs
        (obj,) = inputs
        if not isinstance(obj, list):
            raise TypeError(
                f"ExtractArrangement.instantiate expects object grid, got {type(obj).__name__}"
            )
        return _placements_from_grid(obj)

    def describe(self, inputs: Sequence[Feature], output: Feature, *, step: int) -> str:
        del output, step
        (obj,) = inputs
        return f"Extract arrangement from {obj.refer()}."
