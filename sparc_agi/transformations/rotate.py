from dataclasses import dataclass
from typing import Any

from sparc_agi.geometry import Geometry
from sparc_agi.features.base import Feature
from sparc_agi.features.scalars.orientation import Orientation
from sparc_agi.transformations.base import Transformation, register_transformation

@register_transformation("Rotate")
@dataclass
class Rotate(Transformation):
    """Rotate an object; inputs ``[orientation, object]`` → ``object``.

    Requires the ``orientation`` trait when present. Objects without it
    (e.g. ``Point``) pass through unchanged: no geometric action and no
    step description.
    """

    input_features = ("orientation", "object")
    output_feature = "object"

    def apply(self, inputs: list[Feature], *, step: int, **_: object) -> Feature:
        orientation, obj = inputs
        if not isinstance(orientation, Orientation):
            raise TypeError(f"Rotate expects Orientation, got {type(orientation).__name__}")
        if type(obj).__feature_family__ != "object":
            raise TypeError(f"Rotate expects an object feature, got {type(obj).__feature_name__}")
        if not obj.has_trait("orientation"):
            out = obj.derived()
            out.alias = obj.refer()
            return out
        previous: Orientation = obj.orientation
        out = obj.derived(orientation=orientation.applied_to(previous))
        out.alias = orientation.result_alias(out.kind_noun(), step)
        return out

    def instantiate(
        self,
        inputs: list[Any],
        *,
        step: int,
        feature_inputs: list[Feature] | None = None,
        feature_output: Feature | None = None,
    ) -> Geometry:
        del step, feature_output
        orientation, obj = inputs
        if not isinstance(orientation, int):
            raise TypeError(
                f"Rotate.instantiate expects int orientation, got {type(orientation).__name__}"
            )
        if not isinstance(obj, Geometry):
            raise TypeError(
                f"Rotate.instantiate expects Geometry, got {type(obj).__name__}"
            )
        if feature_inputs is not None:
            _, obj_feat = feature_inputs
            if not obj_feat.has_trait("orientation"):
                return obj
        return obj.apply_orientation(orientation)

    def describe(self, inputs: list[Feature], output: Feature, *, step: int) -> str:
        del output, step
        orientation, obj = inputs
        if not isinstance(orientation, Orientation):
            raise TypeError(f"Rotate expects Orientation, got {type(orientation).__name__}")
        if not obj.has_trait("orientation"):
            return ""
        return orientation.action_sentence(obj.refer())
