from dataclasses import dataclass
from typing import Any

from sparc_agi.geometry import Geometry
from sparc_agi.features.arrangements.base import Arrangement
from sparc_agi.features.base import Feature
from sparc_agi.grid import Placement
from sparc_agi.transformations.base import Transformation, register_transformation

def _placements_from_geometry(geom: Geometry) -> list[Placement]:
    """Occupied positive cells as pool-index-0 placements (local to geom)."""
    out: list[Placement] = []
    for x, y, c in geom.as_root().render():
        if c is not None and c > 0:
            out.append(((x, y), 0))
    return out

@register_transformation("ExtractArrangement")
@dataclass
class ExtractArrangement(Transformation):
    """Pull a read-only arrangement off an object; inputs ``[object]`` → ``arrangement``.

    At instantiate time, recovers placements from occupied cells of the object
    geometry (so sampled glyph patterns are preserved for later mapping/arrange).
    """

    input_features = ("object",)
    output_feature = "arrangement"

    def apply(self, inputs: list[Feature], *, step: int, **_: object) -> Feature:
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
        out.alias = f"arrangement extracted on step {step}"
        return out

    def instantiate(
        self,
        inputs: list[Any],
        *,
        step: int,
        feature_inputs: list[Feature] | None = None,
        feature_output: Feature | None = None,
    ) -> list[Placement]:
        del step, feature_inputs, feature_output
        (obj,) = inputs
        if not isinstance(obj, Geometry):
            raise TypeError(
                f"ExtractArrangement.instantiate expects Geometry, got {type(obj).__name__}"
            )
        return _placements_from_geometry(obj)

    def describe(self, inputs: list[Feature], output: Feature, *, step: int) -> str:
        del output, step
        (obj,) = inputs
        return f"Extract arrangement from {obj.refer()}."
