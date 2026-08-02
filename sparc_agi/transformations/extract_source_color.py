from dataclasses import dataclass
from typing import Any

from sparc_agi.geometry import Geometry
from sparc_agi.features.base import Feature
from sparc_agi.features.scalars.color import Color
from sparc_agi.range import Range
from sparc_agi.transformations.base import Transformation, register_transformation

@register_transformation("ExtractSourceColor")
@dataclass
class ExtractSourceColor(Transformation):
    """Read ``geometry.source.color`` from a sourced object instance.

    Inputs ``[object]`` → ``color``. Requires ``geometry.source`` (donor) with a
    non-``None`` ``color``; otherwise raises.
    """

    input_features = ("object",)
    output_feature = "color"

    def apply(self, inputs: list[Feature], *, step: int, **_: object) -> Feature:
        (obj,) = inputs
        if type(obj).__feature_family__ != "object":
            raise TypeError(
                f"ExtractSourceColor expects an object feature, got {type(obj).__feature_name__}"
            )
        out = Color(value=Range(0, 9))
        out.alias = f"hidden color from step {step}"
        return out

    def instantiate(
        self,
        inputs: list[Any],
        *,
        step: int,
        feature_inputs: list[Feature] | None = None,
        feature_output: Feature | None = None,
    ) -> int:
        del step, feature_inputs, feature_output
        (obj,) = inputs
        if not isinstance(obj, Geometry):
            raise TypeError(
                f"ExtractSourceColor.instantiate expects Geometry, got {type(obj).__name__}"
            )
        if obj.source is None:
            raise ValueError(
                "ExtractSourceColor: geometry has no source "
                "(object must be instantiated from a source)"
            )
        if obj.source.color is None:
            raise ValueError(
                "ExtractSourceColor: geometry.source has no color"
            )
        return obj.source.color

    def describe(self, inputs: list[Feature], output: Feature, *, step: int) -> str:
        del output, step
        (obj,) = inputs
        return f"Extract hidden color from {obj.refer()}."
