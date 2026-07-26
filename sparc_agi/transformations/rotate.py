from dataclasses import dataclass

from sparc_agi.transformations.base import Transformation, register_transformation


@register_transformation("Rotate")
@dataclass
class Rotate(Transformation):
    """Rotate an object; inputs ``[orientation, object]`` → ``object``."""

    input_features = ("orientation", "object")
    output_feature = "object"
