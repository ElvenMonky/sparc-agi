from collections.abc import Sequence
from dataclasses import dataclass

from sparc_agi.features.base import Feature
from sparc_agi.features.orientation import Orientation
from sparc_agi.transformations.base import Transformation, register_transformation


@register_transformation("Rotate")
@dataclass
class Rotate(Transformation):
    """Rotate an object; inputs ``[orientation, object]`` → ``object``."""

    input_features = ("orientation", "object")
    output_feature = "object"

    def apply(self, inputs: Sequence[Feature], *, step: int, **_: object) -> Feature:
        orientation, obj = inputs
        if not isinstance(orientation, Orientation):
            raise TypeError(f"Rotate expects Orientation, got {type(orientation).__name__}")
        if type(obj).__feature_family__ != "object":
            raise TypeError(f"Rotate expects an object feature, got {type(obj).__feature_name__}")
        if not hasattr(obj, "orientation"):
            raise TypeError(f"{type(obj).__name__} has no orientation to rotate")
        previous: Orientation = obj.orientation
        out = obj.derived(orientation=orientation.applied_to(previous))
        out.alias = orientation.result_alias(out.kind_noun(), step)
        return out

    def describe(self, inputs: Sequence[Feature], output: Feature, *, step: int) -> str:
        orientation, obj = inputs
        if not isinstance(orientation, Orientation):
            raise TypeError(f"Rotate expects Orientation, got {type(orientation).__name__}")
        return orientation.action_sentence(obj.refer())
