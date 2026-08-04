from dataclasses import dataclass

from sparc_agi.transformations.base import Transformation, register_transformation

@register_transformation("ChangeColor")
@dataclass
class ChangeColor(Transformation):
    input_features = ("color", "object", "filter")
    output_feature = "object"
